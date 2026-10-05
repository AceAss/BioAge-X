"""
Graph Neural Network Architectures for BioAge-X.
Implements:
1. GCN (Graph Convolutional Network)
2. GraphSAGE (Sample and Aggregate)
3. GAT (Graph Attention Network)
Supports node-level age score regression and biomarker classification.
"""

from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

from bioage.utils.logger import get_logger

logger = get_logger("bioage.gnn.models")


class GraphConvLayer(nn.Module):
    r"""Normalized symmetric graph convolution layer: H^{(l+1)} = \sigma(\tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2} H^{(l)} W)."""

    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=bias)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        num_nodes = x.size(0)
        if edge_index.size(1) == 0:
            return self.linear(x)

        # Build adjacency matrix with self-loops
        adj = torch.zeros((num_nodes, num_nodes), dtype=torch.float32, device=x.device)
        adj[edge_index[0], edge_index[1]] = 1.0
        adj.fill_diagonal_(1.0)

        # Degree normalization: D^{-1/2} A D^{-1/2}
        deg = torch.sum(adj, dim=1)
        deg_inv_sqrt = torch.pow(deg, -0.5)
        deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.0
        d_mat = torch.diag(deg_inv_sqrt)
        norm_adj = torch.mm(torch.mm(d_mat, adj), d_mat)

        # Message passing + linear transform
        support = self.linear(x)
        output = torch.mm(norm_adj, support)
        return output


class GraphSAGELayer(nn.Module):
    r"""Mean-aggregator GraphSAGE layer: H^{(l+1)} = \sigma(W \cdot [H^{(l)} || Mean(N(v))])."""

    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.linear_self = nn.Linear(in_features, out_features, bias=False)
        self.linear_neigh = nn.Linear(in_features, out_features, bias=False)
        self.bias = nn.Parameter(torch.zeros(out_features))

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        num_nodes = x.size(0)
        if edge_index.size(1) == 0:
            return self.linear_self(x) + self.bias

        adj = torch.zeros((num_nodes, num_nodes), dtype=torch.float32, device=x.device)
        adj[edge_index[0], edge_index[1]] = 1.0
        deg = torch.sum(adj, dim=1, keepdim=True).clamp(min=1.0)
        norm_adj = adj / deg

        neigh_repr = torch.mm(norm_adj, x)
        out = self.linear_self(x) + self.linear_neigh(neigh_repr) + self.bias
        return out


class GATLayer(nn.Module):
    """Single-head Graph Attention Layer with LeakyReLU self-attention."""

    def __init__(self, in_features: int, out_features: int, negative_slope: float = 0.2):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=False)
        self.attn_src = nn.Parameter(torch.zeros(1, out_features))
        self.attn_dst = nn.Parameter(torch.zeros(1, out_features))
        self.leaky_relu = nn.LeakyReLU(negative_slope)
        self.bias = nn.Parameter(torch.zeros(out_features))
        nn.init.xavier_uniform_(self.attn_src)
        nn.init.xavier_uniform_(self.attn_dst)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        num_nodes = x.size(0)
        h = self.linear(x)

        if edge_index.size(1) == 0:
            return h + self.bias

        # Self-loops
        adj = torch.zeros((num_nodes, num_nodes), dtype=torch.float32, device=x.device)
        adj[edge_index[0], edge_index[1]] = 1.0
        adj.fill_diagonal_(1.0)

        # Attention scores
        alpha_src = torch.mm(h, self.attn_src.t())
        alpha_dst = torch.mm(h, self.attn_dst.t())
        attn_matrix = alpha_src + alpha_dst.t()
        attn_matrix = self.leaky_relu(attn_matrix)

        # Mask non-edges with -inf
        mask = (adj == 0)
        attn_matrix = attn_matrix.masked_fill(mask, -1e9)
        attn_weights = F.softmax(attn_matrix, dim=1)

        out = torch.mm(attn_weights, h) + self.bias
        return out


class BioAgeGCN(nn.Module):
    """Two-layer Graph Convolutional Network for node regression."""

    def __init__(self, in_features: int, hidden_dim: int = 32, out_features: int = 1, dropout: float = 0.1):
        super().__init__()
        self.conv1 = GraphConvLayer(in_features, hidden_dim)
        self.conv2 = GraphConvLayer(hidden_dim, out_features)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index)
        h = F.relu(h)
        h = self.dropout(h)
        h = self.conv2(h, edge_index)
        return h


class BioAgeGraphSAGE(nn.Module):
    """Two-layer GraphSAGE network for node regression."""

    def __init__(self, in_features: int, hidden_dim: int = 32, out_features: int = 1, dropout: float = 0.1):
        super().__init__()
        self.conv1 = GraphSAGELayer(in_features, hidden_dim)
        self.conv2 = GraphSAGELayer(hidden_dim, out_features)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index)
        h = F.relu(h)
        h = self.dropout(h)
        h = self.conv2(h, edge_index)
        return h


class BioAgeGAT(nn.Module):
    """Two-layer Graph Attention Network for node regression."""

    def __init__(self, in_features: int, hidden_dim: int = 32, out_features: int = 1, dropout: float = 0.1):
        super().__init__()
        self.conv1 = GATLayer(in_features, hidden_dim)
        self.conv2 = GATLayer(hidden_dim, out_features)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index)
        h = F.elu(h)
        h = self.dropout(h)
        h = self.conv2(h, edge_index)
        return h
