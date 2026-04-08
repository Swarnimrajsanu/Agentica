from typing import List, Dict, Optional, Any
from loguru import logger
import json
import re
from services.llm_services import llm_service


class DecisionTreeBuilder:
    """
    Decision Tree Visualization Builder.
    
    Converts all 30+ debate messages into an interactive visual tree diagram:
    - Every argument is a node
    - Every logical connection is an edge
    - Supports for/pro/con relationships
    - Includes sentiment and confidence data
    """
    
    def __init__(self):
        logger.info("🌳 Decision Tree Builder initialized")
    
    async def build_decision_tree(
        self,
        topic: str,
        messages: List[Dict],
        consensus: Dict
    ) -> Dict:
        """
        Build complete decision tree from simulation messages.
        
        Args:
            topic: Discussion topic
            messages: All agent messages from simulation
            consensus: Consensus data
            
        Returns:
            Tree structure ready for visualization
        """
        logger.info(f"🌳 Building decision tree for: {topic}")
        logger.info(f"   Processing {len(messages)} messages...")
        
        # Step 1: Extract all arguments
        arguments = await self._extract_arguments(topic, messages)
        
        # Step 2: Identify logical connections
        connections = await self._identify_connections(topic, arguments)
        
        # Step 3: Build tree structure
        tree = self._construct_tree(topic, arguments, connections, consensus)
        
        # Step 4: Add metadata for visualization
        tree["metadata"] = {
            "topic": topic,
            "total_nodes": len(arguments),
            "total_edges": len(connections),
            "tree_depth": self._calculate_depth(tree),
            "agents_involved": list(set(msg.get("agent_role", "") for msg in messages)),
            "consensus_level": consensus.get("agreement_level", 0)
        }
        
        logger.info(f"✅ Decision tree built: {len(arguments)} nodes, {len(connections)} edges")
        return tree
    
    async def _extract_arguments(
        self,
        topic: str,
        messages: List[Dict]
    ) -> List[Dict]:
        """Extract individual arguments from messages."""
        
        # Group messages by agent
        agent_messages = {}
        for msg in messages:
            role = msg.get("agent_role", "Unknown")
            if role not in agent_messages:
                agent_messages[role] = []
            agent_messages[role].append(msg)
        
        all_arguments = []
        
        # Process each agent's messages
        for role, msgs in agent_messages.items():
            combined_content = " ".join([m.get("content", "") for m in msgs])
            
            prompt = f"""Extract ALL distinct arguments from this agent's response.

Topic: {topic}
Agent Role: {role}
Agent's Full Response:
{combined_content}

For each argument, identify:
1. The core claim/argument
2. Supporting evidence or reasoning
3. Whether it supports or opposes the topic
4. Strength of argument (0-100)
5. Category (financial, technical, market, strategic, etc.)

Respond in JSON format:
{{
  "arguments": [
    {{
      "id": "arg_1",
      "claim": "the main argument",
      "supporting_evidence": "reasoning or evidence provided",
      "stance": "pro|con|neutral",
      "strength": 0-100,
      "category": "financial|technical|market|strategic|operational|regulatory",
      "agent_role": "{role}",
      "round": 0,
      "quotes": ["exact quote 1", "exact quote 2"]
    }}
  ]
}}"""
            
            try:
                result = await llm_service.call_llm(
                    prompt=prompt,
                    system_prompt="You are an argument analyst. Extract every distinct point made.",
                    temperature=0.3,
                    max_tokens=800
                )
                
                if result:
                    data = self._extract_json(result)
                    arguments = data.get("arguments", [])
                    
                    # Add round information
                    for arg in arguments:
                        arg["round"] = msgs[0].get("round", 0) if msgs else 0
                        arg["agent_role"] = role
                    
                    all_arguments.extend(arguments)
                    
            except Exception as e:
                logger.error(f"Error extracting arguments from {role}: {e}")
        
        # Assign unique IDs
        for i, arg in enumerate(all_arguments, 1):
            arg["id"] = f"arg_{i}"
            arg["node_id"] = f"node_{i}"
        
        return all_arguments
    
    async def _identify_connections(
        self,
        topic: str,
        arguments: List[Dict]
    ) -> List[Dict]:
        """Identify logical connections between arguments."""
        
        # Prepare arguments text
        args_text = "\n".join([
            f"{arg['id']} ({arg['agent_role']}): {arg['claim']}"
            for arg in arguments[:20]  # Limit to avoid token limits
        ])
        
        prompt = f"""Identify ALL logical connections between these arguments.

Topic: {topic}

Arguments:
{args_text}

For each connection, specify:
1. Source argument ID
2. Target argument ID
3. Relationship type:
   - "supports" (argument A strengthens argument B)
   - "contradicts" (argument A opposes argument B)
   - "elaborates" (argument A adds detail to argument B)
   - "causes" (argument A leads to argument B)
   - "examples" (argument A exemplifies argument B)
   - "challenges" (argument A questions argument B)
4. Strength of connection (0-100)
5. Explanation of the connection

Respond in JSON format:
{{
  "connections": [
    {{
      "source_id": "arg_1",
      "target_id": "arg_3",
      "relationship": "supports|contradicts|elaborates|causes|examples|challenges",
      "strength": 0-100,
      "explanation": "why these are connected"
    }}
  ]
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a logic analyst. Find all relationships between arguments.",
                temperature=0.3,
                max_tokens=1000
            )
            
            if result:
                data = self._extract_json(result)
                return data.get("connections", [])
            
            return []
        except Exception as e:
            logger.error(f"Error identifying connections: {e}")
            return []
    
    def _construct_tree(
        self,
        topic: str,
        arguments: List[Dict],
        connections: List[Dict],
        consensus: Dict
    ) -> Dict:
        """Construct hierarchical tree structure."""
        
        # Create root node (the main topic/question)
        root = {
            "id": "root",
            "node_id": "root",
            "claim": topic,
            "type": "root",
            "stance": "neutral",
            "strength": 100,
            "category": "topic",
            "agent_role": "System",
            "round": 0,
            "children": [],
            "metadata": {
                "consensus_level": consensus.get("agreement_level", 0),
                "total_arguments": len(arguments)
            }
        }
        
        # Group arguments by stance
        pro_args = [arg for arg in arguments if arg.get("stance") == "pro"]
        con_args = [arg for arg in arguments if arg.get("stance") == "con"]
        neutral_args = [arg for arg in arguments if arg.get("stance") == "neutral"]
        
        # Create PRO branch
        if pro_args:
            pro_node = {
                "id": "branch_pro",
                "node_id": "branch_pro",
                "claim": "Arguments IN FAVOR",
                "type": "branch",
                "stance": "pro",
                "strength": int(sum(a.get("strength", 50) for a in pro_args) / len(pro_args)),
                "category": "summary",
                "agent_role": "Aggregation",
                "round": 0,
                "children": self._organize_subtree(pro_args, connections),
                "metadata": {
                    "argument_count": len(pro_args),
                    "avg_strength": int(sum(a.get("strength", 50) for a in pro_args) / len(pro_args))
                }
            }
            root["children"].append(pro_node)
        
        # Create CON branch
        if con_args:
            con_node = {
                "id": "branch_con",
                "node_id": "branch_con",
                "claim": "Arguments AGAINST",
                "type": "branch",
                "stance": "con",
                "strength": int(sum(a.get("strength", 50) for a in con_args) / len(con_args)),
                "category": "summary",
                "agent_role": "Aggregation",
                "round": 0,
                "children": self._organize_subtree(con_args, connections),
                "metadata": {
                    "argument_count": len(con_args),
                    "avg_strength": int(sum(a.get("strength", 50) for a in con_args) / len(con_args))
                }
            }
            root["children"].append(con_node)
        
        # Create NEUTRAL branch
        if neutral_args:
            neutral_node = {
                "id": "branch_neutral",
                "node_id": "branch_neutral",
                "claim": "Neutral Observations",
                "type": "branch",
                "stance": "neutral",
                "strength": 50,
                "category": "summary",
                "agent_role": "Aggregation",
                "round": 0,
                "children": self._organize_subtree(neutral_args, connections),
                "metadata": {
                    "argument_count": len(neutral_args)
                }
            }
            root["children"].append(neutral_node)
        
        # Add connections as edge data
        root["edges"] = self._format_edges(connections)
        
        return root
    
    def _organize_subtree(
        self,
        arguments: List[Dict],
        connections: List[Dict]
    ) -> List[Dict]:
        """Organize arguments into logical subtree by category."""
        
        # Group by category
        by_category = {}
        for arg in arguments:
            category = arg.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(arg)
        
        subtree = []
        for category, args in by_category.items():
            # Sort by strength
            args.sort(key=lambda x: x.get("strength", 50), reverse=True)
            
            category_node = {
                "id": f"category_{category}",
                "node_id": f"category_{category}",
                "claim": f"{category.title()} Arguments",
                "type": "category",
                "stance": args[0].get("stance", "neutral") if args else "neutral",
                "strength": int(sum(a.get("strength", 50) for a in args) / len(args)) if args else 50,
                "category": category,
                "agent_role": "Category",
                "round": 0,
                "children": args,  # Leaf nodes
                "metadata": {
                    "argument_count": len(args)
                }
            }
            subtree.append(category_node)
        
        return subtree
    
    def _format_edges(self, connections: List[Dict]) -> List[Dict]:
        """Format connections for visualization."""
        edges = []
        for conn in connections:
            edges.append({
                "source": conn.get("source_id", ""),
                "target": conn.get("target_id", ""),
                "relationship": conn.get("relationship", "supports"),
                "strength": conn.get("strength", 50),
                "label": conn.get("explanation", ""),
                "color": self._get_edge_color(conn.get("relationship", ""))
            })
        return edges
    
    def _get_edge_color(self, relationship: str) -> str:
        """Get color code for edge based on relationship type."""
        colors = {
            "supports": "#4ade80",      # Green
            "contradicts": "#f87171",   # Red
            "elaborates": "#60a5fa",    # Blue
            "causes": "#fbbf24",        # Yellow
            "examples": "#c084fc",      # Purple
            "challenges": "#fb923c"     # Orange
        }
        return colors.get(relationship, "#94a3b8")
    
    def _calculate_depth(self, tree: Dict, current_depth: int = 0) -> int:
        """Calculate maximum depth of tree."""
        if not tree.get("children"):
            return current_depth
        
        max_depth = current_depth
        for child in tree.get("children", []):
            depth = self._calculate_depth(child, current_depth + 1)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
        return {}
    
    def generate_d3_format(self, tree: Dict) -> Dict:
        """Convert tree to D3.js compatible format."""
        nodes = []
        links = []
        
        def traverse(node, parent_id=None):
            nodes.append({
                "id": node.get("node_id", node.get("id")),
                "label": node.get("claim", "")[:100],
                "type": node.get("type", "argument"),
                "stance": node.get("stance", "neutral"),
                "strength": node.get("strength", 50),
                "category": node.get("category", ""),
                "agent_role": node.get("agent_role", ""),
                "metadata": node.get("metadata", {})
            })
            
            if parent_id:
                links.append({
                    "source": parent_id,
                    "target": node.get("node_id", node.get("id"))
                })
            
            for child in node.get("children", []):
                traverse(child, node.get("node_id", node.get("id")))
        
        traverse(tree)
        
        # Add edges from tree
        if "edges" in tree:
            links.extend(tree["edges"])
        
        return {
            "nodes": nodes,
            "links": links
        }


# Global decision tree builder instance
decision_tree_builder = DecisionTreeBuilder()
