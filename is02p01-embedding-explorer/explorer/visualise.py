"""explorer/visualise.py - High-dimensional vector space projection to 2D using UMAP."""

import numpy as np
import umap
import matplotlib

# Headless mode for WSL/Linux environments without display servers
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .store import VectorStore


def visualise(
    store: VectorStore,
    output_path: str = "embedding_space.png",
    groups: list[str] | None = None,
) -> str:
    """Project all stored embeddings to 2D with UMAP and save a PNG.

    Reads every embedding from the store, fits a 2-component UMAP reducer,
    and plots each point labeled with a truncated version of its text.
    If groups are provided, points are colored by topic and a legend is added.

    Args:
        store: A populated VectorStore. Must contain at least 3 items.
        output_path: File path for the saved PNG visualization.
        groups: Optional list of topic label strings, one per stored text,
            in the same order as texts were added to the store.

    Returns:
        The resolved output path string.

    Raises:
        ValueError: If the store contains fewer than 3 items.
    """
    data = store.get_all()
    texts = data["texts"]
    embeddings = np.array(data["embeddings"])  # shape: (n, 384)

    n = len(texts)
    if n < 3:
        raise ValueError(f"Need at least 3 points to visualise, got {n}.")

    # n_neighbors must be < number of points; cap it dynamically to avoid crash
    n_neighbors = min(15, n - 1)

    # Use cosine metric for semantic vectors
    reducer = umap.UMAP(
        n_components=2,
        random_state=42,
        n_neighbors=n_neighbors,
        min_dist=0.1,
        metric="cosine",
    )
    coords = reducer.fit_transform(embeddings)  # shape: (n, 2)

    # Set up dark theme matching the curriculum style
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_facecolor("#0D1117")
    fig.patch.set_facecolor("#0D1117")

    xs, ys = coords[:, 0], coords[:, 1]

    if groups is not None:
        unique = sorted(set(groups))
        cmap = plt.get_cmap("tab10")
        color_of = {g: cmap(i % 10) for i, g in enumerate(unique)}
        point_colors = [color_of[g] for g in groups]
        ax.scatter(xs, ys, s=110, c=point_colors, edgecolors="#1E293B", zorder=2)
        
        handles = [
            plt.Line2D(
                [0], [0],
                marker="o",
                linestyle="",
                markerfacecolor=color_of[g],
                markeredgecolor="#1E293B",
                markersize=10,
                label=g,
            )
            for g in unique
        ]
        ax.legend(
            handles=handles,
            loc="best",
            facecolor="#161B22",
            edgecolor="#30363D",
            labelcolor="#C9D1D9",
            fontsize=9,
        )
    else:
        ax.scatter(xs, ys, s=110, color="#818CF8", edgecolors="#1E293B", zorder=2)

    # Annotate points with truncated text labels
    for text, x, y in zip(texts, xs, ys):
        label = text if len(text) <= 32 else text[:29] + "..."
        ax.annotate(
            label,
            (x, y),
            fontsize=7,
            color="#94A3B8",
            xytext=(6, 4),
            textcoords="offset points",
        )

    ax.set_title("Embedding Space — 2D UMAP Projection", color="#F1F5F9", fontsize=13)
    ax.tick_params(colors="#475569")

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved visualisation -> {output_path} ({n} points, n_neighbors={n_neighbors})")
    return output_path
