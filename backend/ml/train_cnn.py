"""Train a PlantVillage CNN classifier with leakage-safe HF splits.

Usage example:
  python backend/ml/train_cnn.py --subset color --epochs 20 --batch-size 32
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import numpy as np
import tensorflow as tf
from datasets import load_dataset
from PIL import Image
from sklearn.metrics import classification_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subset",
        type=str,
        default="auto",
        choices=["auto", "default", "color", "grayscale", "segmented"],
        help="PlantVillage config name. Use 'auto' to try color first, then fallback to default.",
    )
    parser.add_argument("--image-size", type=int, default=380)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="backend/models")
    parser.add_argument("--weights", type=str, default="imagenet", choices=["imagenet", "none"])
    return parser.parse_args()


def _infer_text_row(row_text: str):
    raw = row_text.strip()
    if not raw:
        return None, None

    # JSON payload rows
    if raw.startswith("{") and raw.endswith("}"):
        try:
            payload = json.loads(raw)
            image_path = payload.get("image") or payload.get("path") or payload.get("filepath")
            label = payload.get("label") or payload.get("class") or payload.get("disease")
            return image_path, label
        except Exception:
            pass

    # "label,path" or "label\tpath"
    for sep in ("\t", ",", ";"):
        if sep in raw:
            left, right = raw.split(sep, 1)
            left = left.strip().strip('"')
            right = right.strip().strip('"')
            if re.search(r"\.(jpg|jpeg|png|bmp)$", right, flags=re.IGNORECASE):
                return right, left
            if re.search(r"\.(jpg|jpeg|png|bmp)$", left, flags=re.IGNORECASE):
                return left, right

    # Path-only row
    if re.search(r"\.(jpg|jpeg|png|bmp)$", raw, flags=re.IGNORECASE):
        return raw, None

    return None, None


def _resolve_image_path(path_text: str, repo_root: Path):
    candidates = [
        Path(path_text),
        Path.cwd() / path_text,
        repo_root / path_text,
        repo_root / "datasets" / "images" / path_text,
        repo_root / "datasets" / "images" / "raw" / path_text,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def resolve_columns_and_labels(train_split, test_split):
    image_col = None
    label_col = None

    for col, feature in train_split.features.items():
        if image_col is None and feature.__class__.__name__ == "Image":
            image_col = col
        if label_col is None and hasattr(feature, "names"):
            label_col = col

    if image_col is None:
        for candidate in ("image", "img", "leaf_image"):
            if candidate in train_split.column_names:
                image_col = candidate
                break

    if label_col is None:
        for candidate in ("label", "class", "disease", "category", "target"):
            if candidate in train_split.column_names:
                label_col = candidate
                break

    if image_col is None or label_col is None:
        # Fallback for HF cache variants that expose a text manifest.
        if train_split.column_names == ["text"]:
            repo_root = Path(__file__).resolve().parents[2]
            all_rows = []
            for split_name, split_data in (("train", train_split), ("test", test_split)):
                for row in split_data:
                    image_raw, label_raw = _infer_text_row(row["text"])
                    if image_raw is None:
                        continue
                    image_path = _resolve_image_path(image_raw, repo_root)
                    if image_path is None:
                        continue
                    if label_raw is None:
                        label_raw = image_path.parent.name
                    all_rows.append((split_name, str(image_path), str(label_raw)))

            if not all_rows:
                raise ValueError(
                    "Dataset exposed only 'text' rows, but no image paths could be resolved. "
                    "Please extract PlantVillage under datasets/images/ and retry."
                )

            labels = sorted({row[2] for row in all_rows})
            label_to_id = {name: idx for idx, name in enumerate(labels)}

            train_rows = [(p, label_to_id[l]) for s, p, l in all_rows if s == "train"]
            test_rows = [(p, label_to_id[l]) for s, p, l in all_rows if s == "test"]

            return "manifest_text", "label_id", labels, train_rows, test_rows, None

        raise ValueError(
            f"Could not infer image/label columns from {train_split.column_names}. "
            "If this is a manifest-only cache, extract PlantVillage images and retry."
        )

    feature = train_split.features[label_col]
    if hasattr(feature, "names"):
        label_names = feature.names
        mapped_label_col = label_col
        train_encoded = train_split
        encoder = None
    else:
        sample_value = train_split[0][label_col]
        if isinstance(sample_value, str):
            label_names = sorted(set(train_split[label_col]))
            label_to_id = {name: idx for idx, name in enumerate(label_names)}

            def encoder(example):
                return {"label_id": label_to_id[example[label_col]]}

            train_encoded = train_split.map(encoder)
            mapped_label_col = "label_id"
        else:
            # Fallback for numeric labels stored as plain integers.
            max_label = int(max(train_split[label_col]))
            label_names = [str(i) for i in range(max_label + 1)]
            mapped_label_col = label_col
            train_encoded = train_split
            encoder = None

    if encoder is not None:
        test_encoded = test_split.map(encoder)
    else:
        test_encoded = test_split

    return image_col, mapped_label_col, label_names, train_encoded, test_encoded, encoder


def make_tf_dataset(hf_split, image_col: str, label_col: str, image_size: int, batch_size: int, training: bool, seed: int) -> tf.data.Dataset:
    def gen():
        for sample in hf_split:
            image = sample[image_col].convert("RGB").resize((image_size, image_size))
            x = np.asarray(image, dtype=np.float32)
            y = np.int32(sample[label_col])
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


def make_tf_dataset_from_manifest(rows, image_size: int, batch_size: int, training: bool, seed: int) -> tf.data.Dataset:
    def gen():
        for image_path, label_id in rows:
            with Image.open(image_path) as image:
                image = image.convert("RGB").resize((image_size, image_size))
                x = np.asarray(image, dtype=np.float32)
            y = np.int32(label_id)
            yield x, y

    ds = tf.data.Dataset.from_generator(
        gen,
        output_signature=(
            tf.TensorSpec(shape=(image_size, image_size, 3), dtype=tf.float32),
            tf.TensorSpec(shape=(), dtype=tf.int32),
        ),
    )

    if training:
        ds = ds.shuffle(min(len(rows), 2048), seed=seed, reshuffle_each_iteration=True)

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
    os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[2] / ".hf_cache"))
    os.environ.setdefault("HF_DATASETS_CACHE", str(Path(__file__).resolve().parents[2] / ".hf_cache" / "datasets"))
    if args.subset == "auto":
        try:
            dataset = load_dataset("mohanty/PlantVillage", "color")
            chosen_subset = "color"
        except Exception:
            dataset = load_dataset("mohanty/PlantVillage", "default")
            chosen_subset = "default"
    elif args.subset == "default":
        dataset = load_dataset("mohanty/PlantVillage", "default")
        chosen_subset = "default"
    else:
        dataset = load_dataset("mohanty/PlantVillage", args.subset)
        chosen_subset = args.subset
    print(f"Loaded config: {chosen_subset}")
    train_split = dataset["train"]
    test_split = dataset["test"]

    image_col, label_col, label_names, train_split, test_split, encoder = resolve_columns_and_labels(train_split, test_split)
    num_classes = len(label_names)

    if image_col == "manifest_text":
        train_ds = make_tf_dataset_from_manifest(train_split, args.image_size, args.batch_size, training=True, seed=args.seed)
        test_ds = make_tf_dataset_from_manifest(test_split, args.image_size, args.batch_size, training=False, seed=args.seed)
        train_len = len(train_split)
    else:
        train_ds = make_tf_dataset(train_split, image_col, label_col, args.image_size, args.batch_size, training=True, seed=args.seed)
        test_ds = make_tf_dataset(test_split, image_col, label_col, args.image_size, args.batch_size, training=False, seed=args.seed)
        train_len = len(train_split)

    val_size = max(1, int(0.1 * train_len / args.batch_size))
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
