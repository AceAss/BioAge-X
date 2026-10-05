"""
Graph Dataset Abstraction for BioAge-X.
Converts BiologicalInteractionGraph and biomarker data into PyTorch / PyG tensors:
- Node feature matrix X (degree, centrality, PageRank, omics correlation)
- Edge index tensor E (2 x |E|)
- Node target tensor y (e.g. biological age association or senescence class)
- Train / Val / Test boolean masks
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch

from bioage.network.interaction_graph import BiologicalInteractionGraph
from bioage.utils.logger import get_logger

logger = get_logger("bioage.gnn.graph_dataset")


class BioAgeGraphDataset:
    """Encapsulates node features, graph adjacency, and training masks for PyTorch/PyG GNNs."""

    def __init__(
        self,
        node_ids: List[str],
        x: torch.Tensor,
        edge_index: torch.Tensor,
        y: torch.Tensor,
        train_mask: torch.Tensor,
        val_mask: torch.Tensor,
        test_mask: torch.Tensor,
        feature_names: List[str],
    ):
        self.node_ids = node_ids
        self.x = x
        self.edge_index = edge_index
        self.y = y
        self.train_mask = train_mask
        self.val_mask = val_mask
        self.test_mask = test_mask
        self.feature_names = feature_names

    @property
    def num_nodes(self) -> int:
        return self.x.shape[0]

    @property
    def num_edges(self) -> int:
        return self.edge_index.shape[1]

    @classmethod
    def from_interaction_graph(
        self,
        bio_graph: BiologicalInteractionGraph,
        target_dict: Optional[Dict[str, float]] = None,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        random_seed: int = 42,
    ) -> "BioAgeGraphDataset":
        """Builds dataset from BiologicalInteractionGraph."""
        nodes = list(bio_graph.graph.nodes())
        n_nodes = len(nodes)
        node_to_idx = {n: i for i, n in enumerate(nodes)}

        # Features: [degree_centrality, betweenness_centrality, pagerank, is_biomarker_flag, node_type_onehot]
        feature_names = ["degree_centrality", "betweenness_centrality", "pagerank", "is_biomarker"]
        feature_rows = []
        targets = []

        rng = np.random.default_rng(random_seed)

        for n in nodes:
            metrics = bio_graph.topological_metrics_.get(n, {})
            data = bio_graph.graph.nodes[n]
            is_bio = 1.0 if data.get("is_biomarker", False) else 0.0

            deg_c = float(metrics.get("degree_centrality", 0.0))
            bet_c = float(metrics.get("betweenness_centrality", 0.0))
            p_rank = float(metrics.get("pagerank", 0.0))

            feature_rows.append([deg_c, bet_c, p_rank, is_bio])

            # Node regression target: age association strength
            if target_dict and n in target_dict:
                targets.append(float(target_dict[n]))
            else:
                # Synthetic target based on centrality + biomarker status + slight noise
                synth_target = 0.5 * is_bio + 0.3 * p_rank * 10 + rng.normal(0, 0.1)
                targets.append(float(synth_target))

        x_tensor = torch.tensor(feature_rows, dtype=torch.float32)
        y_tensor = torch.tensor(targets, dtype=torch.float32).unsqueeze(1)

        # Edges
        edges = list(bio_graph.graph.edges())
        if edges:
            src_list = []
            dst_list = []
            for u, v in edges:
                u_idx, v_idx = node_to_idx[u], node_to_idx[v]
                # Undirected: add both u->v and v->u
                src_list.extend([u_idx, v_idx])
                dst_list.extend([v_idx, u_idx])
            edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)

        # Masks
        indices = np.arange(n_nodes)
        rng.shuffle(indices)
        n_train = max(1, int(train_ratio * n_nodes))
        n_val = max(1, int(val_ratio * n_nodes))

        train_indices = set(indices[:n_train])
        val_indices = set(indices[n_train:n_train + n_val])
        test_indices = set(indices[n_train + n_val:])

        train_mask = torch.tensor([i in train_indices for i in range(n_nodes)], dtype=torch.bool)
        val_mask = torch.tensor([i in val_indices for i in range(n_nodes)], dtype=torch.bool)
        test_mask = torch.tensor([i in test_indices for i in range(n_nodes)], dtype=torch.bool)

        logger.info(
            f"Created BioAgeGraphDataset: {n_nodes} nodes, {edge_index.shape[1]} directed edges, "
            f"{train_mask.sum().item()} train, {val_mask.sum().item()} val, {test_mask.sum().item()} test"
        )

        return BioAgeGraphDataset(
            node_ids=nodes,
            x=x_tensor,
            edge_index=edge_index,
            y=y_tensor,
            train_mask=train_mask,
            val_mask=val_mask,
            test_mask=test_mask,
            feature_names=feature_names,
        )
