"""
GNN Trainer and Evaluator for BioAge-X.
Trains GCN, GraphSAGE, and GAT models on biological interaction graphs.
Labels experimental predictions clearly as computational hypotheses.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from bioage.gnn.graph_dataset import BioAgeGraphDataset
from bioage.gnn.models import BioAgeGCN, BioAgeGraphSAGE, BioAgeGAT
from bioage.utils.logger import get_logger

logger = get_logger("bioage.gnn.trainer")

GNN_SCIENTIFIC_DISCLAIMER = (
    "NOTICE: GNN predictions are experimental computational hypotheses derived from topological "
    "network propagation and multi-omics priors. They do not constitute experimentally validated "
    "biological mechanisms."
)


class GraphTrainer:
    """Trains graph neural network architectures on BioAgeGraphDataset."""

    def __init__(
        self,
        model: nn.Module,
        dataset: BioAgeGraphDataset,
        lr: float = 0.01,
        weight_decay: float = 5e-4,
        random_seed: Optional[int] = None,
    ):
        if random_seed is not None:
            torch.manual_seed(random_seed)
            np.random.seed(random_seed)

        self.model = model
        self.dataset = dataset
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        self.criterion = nn.MSELoss()
        self.history_: Dict[str, List[float]] = {"train_loss": [], "val_loss": []}

    def train(self, epochs: int = 60) -> Dict[str, List[float]]:
        logger.info(f"Training {self.model.__class__.__name__} for {epochs} epochs")
        self.model.train()

        for epoch in range(1, epochs + 1):
            self.optimizer.zero_grad()
            out = self.model(self.dataset.x, self.dataset.edge_index)
            loss = self.criterion(out[self.dataset.train_mask], self.dataset.y[self.dataset.train_mask])
            loss.backward()
            self.optimizer.step()

            # Validation loss
            self.model.eval()
            with torch.no_grad():
                val_out = self.model(self.dataset.x, self.dataset.edge_index)
                if self.dataset.val_mask.sum() > 0:
                    val_loss = self.criterion(val_out[self.dataset.val_mask], self.dataset.y[self.dataset.val_mask]).item()
                else:
                    val_loss = loss.item()

            self.history_["train_loss"].append(round(loss.item(), 4))
            self.history_["val_loss"].append(round(val_loss, 4))
            self.model.train()

            if epoch % 20 == 0 or epoch == epochs:
                logger.info(f"Epoch {epoch:03d} | Train Loss: {loss.item():.4f} | Val Loss: {val_loss:.4f}")

        return self.history_


class GraphEvaluator:
    """Evaluates GNN models and produces node-level predictions."""

    @staticmethod
    def evaluate(model: nn.Module, dataset: BioAgeGraphDataset) -> Dict[str, Any]:
        model.eval()
        with torch.no_grad():
            preds = model(dataset.x, dataset.edge_index).squeeze().numpy()

        y_true = dataset.y.squeeze().numpy()
        test_mask = dataset.test_mask.numpy()

        if test_mask.sum() > 0:
            test_true = y_true[test_mask]
            test_preds = preds[test_mask]
            mse = float(mean_squared_error(test_true, test_preds))
            mae = float(mean_absolute_error(test_true, test_preds))
            r2 = float(r2_score(test_true, test_preds)) if len(test_true) > 2 else 0.0
        else:
            mse = float(mean_squared_error(y_true, preds))
            mae = float(mean_absolute_error(y_true, preds))
            r2 = float(r2_score(y_true, preds))

        # Sort node predictions
        node_scores = []
        for i, node_id in enumerate(dataset.node_ids):
            node_scores.append({
                "node_id": node_id,
                "predicted_score": round(float(preds[i]), 3),
                "true_score": round(float(y_true[i]), 3),
                "is_biomarker": bool(dataset.x[i, 3].item() > 0.5),
            })

        node_scores = sorted(node_scores, key=lambda x: x["predicted_score"], reverse=True)

        return {
            "model_architecture": model.__class__.__name__,
            "test_mse": round(mse, 4),
            "test_mae": round(mae, 4),
            "test_r2": round(r2, 4),
            "top_predicted_nodes": node_scores[:15],
            "all_node_predictions": node_scores,
            "disclaimer": GNN_SCIENTIFIC_DISCLAIMER,
        }
