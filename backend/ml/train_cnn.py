"""Train a PlantVillage CNN classifier with leakage-safe HF splits.

Usage example:
  python backend/ml/train_cnn.py --subset color --epochs 20 --batch-size 32
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from datasets import load_dataset
from sklearn.metrics import classification_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", type=str, default="color", choices=["color", "grayscale", "segmented"])
    parser.add_argument("--image-size", type=int, default=380)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="backend/models")
    parser.add_argument("--weights", type=str, default="imagenet", choices=["imagenet", "none"])
    return parser.parse_args()


def make_tf_dataset(hf_split, image_size: int, batch_size: int, training: bool, seed: int) -> tf.data.Dataset:
    def gen():
        for sample in hf_split:
            image = sample["image"].convert("RGB").resize((image_size, image_size))
            x = np.asarray(image, dtype=np.float32)
            y = np.int32(sample["label"])
            yield x, y

    ds = tf.data.Dataset.from_generator(
        gen,
        output_signature=(
            tf.TensorSpec(shape=(image_size, image_size, 3), dtype=tf.float32),
            tf.TensorSpec(shape=(), dtype=tf.int32),
        ),
    )

    if training:
        ds = ds.shuffle(min(len(hf_split), 2048), seed=seed, reshuffle_each_iteration=True)

    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


def build_model(num_classes: int, image_size: int, lr: float, weight_decay: float, use_imagenet: bool) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(image_size, image_size, 3))

    augment = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.1),
            tf.keras.layers.RandomZoom(0.15),
            tf.keras.layers.RandomContrast(0.1),
        ],
        name="augment",
    )

    x = augment(inputs)
    x = tf.keras.applications.efficientnet.preprocess_input(x)

    weights = "imagenet" if use_imagenet else None
    try:
        backbone = tf.keras.applications.EfficientNetB4(
            include_top=False,
            weights=weights,
            input_tensor=x,
            pooling="avg",
        )
    except Exception:
        # Fallback when pretrained weights cannot be fetched.
        backbone = tf.keras.applications.EfficientNetB4(
            include_top=False,
            weights=None,
            input_tensor=x,
            pooling="avg",
        )

    backbone.trainable = False

    x = tf.keras.layers.Dropout(0.3)(backbone.output)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="disease_class")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="plantvillage_efficientnetb4")
    optimizer = tf.keras.optimizers.AdamW(learning_rate=lr, weight_decay=weight_decay)
    model.compile(
        optimizer=optimizer,
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )

    return model


def main() -> None:
    args = parse_args()
    tf.keras.utils.set_random_seed(args.seed)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading PlantVillage subset={args.subset}...")
    dataset = load_dataset("mohanty/PlantVillage", args.subset)
    train_split = dataset["train"]
    test_split = dataset["test"]

    label_names = train_split.features["label"].names
    num_classes = len(label_names)

    train_ds = make_tf_dataset(train_split, args.image_size, args.batch_size, training=True, seed=args.seed)
    test_ds = make_tf_dataset(test_split, args.image_size, args.batch_size, training=False, seed=args.seed)

    val_size = max(1, int(0.1 * len(train_split) / args.batch_size))
    val_ds = train_ds.take(val_size)
    fit_train_ds = train_ds.skip(val_size)

    model = build_model(
        num_classes=num_classes,
        image_size=args.image_size,
        lr=args.lr,
        weight_decay=args.weight_decay,
        use_imagenet=args.weights == "imagenet",
    )

    ckpt_path = out_dir / "best_plantvillage_efficientnetb4.keras"
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(str(ckpt_path), monitor="val_accuracy", save_best_only=True, verbose=1),
        tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.4, patience=2, min_lr=1e-6),
    ]

    history = model.fit(
        fit_train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=callbacks,
        verbose=1,
    )

    print("\nFine-tuning backbone...")
    model.get_layer("efficientnetb4").trainable = True
    model.compile(
        optimizer=tf.keras.optimizers.AdamW(learning_rate=args.lr * 0.1, weight_decay=args.weight_decay),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )

    model.fit(
        fit_train_ds,
        validation_data=val_ds,
        epochs=max(3, args.epochs // 3),
        callbacks=callbacks,
        verbose=1,
    )

    test_loss, test_acc = model.evaluate(test_ds, verbose=0)
    print(f"Test accuracy: {test_acc:.4f} | Test loss: {test_loss:.4f}")

    y_true, y_pred = [], []
    for x_batch, y_batch in test_ds:
        probs = model.predict(x_batch, verbose=0)
        y_true.extend(y_batch.numpy().tolist())
        y_pred.extend(np.argmax(probs, axis=1).tolist())

    report = classification_report(
        y_true,
        y_pred,
        target_names=label_names,
        digits=4,
        output_dict=True,
        zero_division=0,
    )

    with open(out_dir / "label_map.json", "w", encoding="utf-8") as f:
        json.dump({"labels": label_names}, f, indent=2)

    with open(out_dir / "metrics_report.json", "w", encoding="utf-8") as f:
        json.dump({"test_loss": float(test_loss), "test_accuracy": float(test_acc), "report": report}, f, indent=2)

    with open(out_dir / "history.json", "w", encoding="utf-8") as f:
        json.dump(history.history, f, indent=2)

    final_model = out_dir / "plantvillage_efficientnetb4_final.keras"
    model.save(final_model)
    print(f"Saved model to {final_model}")


if __name__ == "__main__":
    main()
