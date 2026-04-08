from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class HeatmapResult:
    agents: List[str]
    matrix: List[List[float]]


class ConsensusHeatmapService:
    """
    Computes pairwise agreement scores between agents for a given round.

    Agreement is a lightweight lexical similarity (Jaccard over token sets)
    to keep this dependency-free and fast enough for per-round updates.
    """

    _stopwords: Set[str] = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "has",
        "have",
        "he",
        "her",
        "his",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "me",
        "my",
        "not",
        "of",
        "on",
        "or",
        "our",
        "she",
        "so",
        "such",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "to",
        "we",
        "were",
        "will",
        "with",
        "you",
        "your",
    }

    def compute_round_heatmap(self, *, messages: List[Dict], round_num: int) -> HeatmapResult:
        # Collect last message per agent for the round (agents speak once per round)
        by_agent: Dict[str, str] = {}
        for msg in messages:
            if msg.get("round") != round_num:
                continue
            role = (msg.get("agent_role") or "Unknown").strip()
            content = (msg.get("content") or "").strip()
            if role:
                by_agent[role] = content

        agents = sorted(by_agent.keys())
        tokens: Dict[str, Set[str]] = {a: self._tokenize(by_agent[a]) for a in agents}

        matrix: List[List[float]] = []
        for i, a_i in enumerate(agents):
            row: List[float] = []
            for j, a_j in enumerate(agents):
                if i == j:
                    row.append(1.0)
                else:
                    row.append(self._jaccard(tokens[a_i], tokens[a_j]))
            matrix.append(row)

        return HeatmapResult(agents=agents, matrix=matrix)

    def _tokenize(self, text: str) -> Set[str]:
        cleaned = []
        for ch in text.lower():
            cleaned.append(ch if (ch.isalnum() or ch.isspace()) else " ")
        parts = "".join(cleaned).split()
        return {p for p in parts if len(p) >= 3 and p not in self._stopwords}

    def _jaccard(self, a: Set[str], b: Set[str]) -> float:
        if not a and not b:
            return 0.0
        inter = a.intersection(b)
        union = a.union(b)
        return float(len(inter)) / float(len(union)) if union else 0.0


consensus_heatmap_service = ConsensusHeatmapService()

