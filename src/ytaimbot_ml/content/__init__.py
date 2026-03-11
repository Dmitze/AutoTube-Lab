"""Phase 2 — Content Generation package.

Modules
-------
script_generator  : ScriptGenerator — LLM-based script assembly
token_budget      : TokenBudget — DP knapsack for token allocation

Algorithm
---------
Token budget allocation: 0/1 Knapsack DP → O(n × W)
Script assembly: template + LLM chain → O(n_sections × tokens)

Status: 🔲 Pending — T-123 (Phase 2, EPIC 2.4)
"""
