from neo4j import GraphDatabase
from loguru import logger
from config.settings import settings


class GraphService:
    """Neo4j Graph Database Service for GraphRAG operations."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        logger.info("Neo4j connection established")
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def get_graph_context(self, query: str, limit: int = 10):
        """
        Retrieve graph context from Neo4j.
        
        Args:
            query: Custom Cypher query or topic to search
            limit: Maximum number of results to return
            
        Returns:
            List of graph relationships
        """
        try:
            with self.driver.session() as session:
                # Default query - can be customized based on use case
                cypher_query = """
                MATCH (n)-[r]->(m)
                WHERE n['name'] CONTAINS $search_term OR m['name'] CONTAINS $search_term
                RETURN n, r, m
                LIMIT $limit
                """
                
                result = session.run(
                    cypher_query,
                    search_term=query,
                    limit=limit
                )
                
                records = []
                for record in result:
                    records.append({
                        "node": dict(record["n"]),
                        "relationship": dict(record["r"]),
                        "related_node": dict(record["m"])
                    })
                
                logger.info(f"Retrieved {len(records)} graph relationships")
                return records
                
        except Exception as e:
            logger.error(f"Error retrieving graph context: {e}")
            return []
    
    def add_node(self, label: str, properties: dict):
        """
        Add a node to the graph.
        
        Args:
            label: Node label (type)
            properties: Node properties
            
        Returns:
            Created node data
        """
        try:
            with self.driver.session() as session:
                query = f"CREATE (n:{label} $props) RETURN n"
                result = session.run(query, props=properties)
                record = result.single()
                logger.info(f"Added node with label {label}")
                return dict(record["n"]) if record else None
        except Exception as e:
            logger.error(f"Error adding node: {e}")
            return None
    
    def add_relationship(self, from_node_id: str, to_node_id: str, relationship_type: str, properties: dict = None):
        """
        Add a relationship between two nodes.
        
        Args:
            from_node_id: ID of the source node
            to_node_id: ID of the target node
            relationship_type: Type of relationship
            properties: Relationship properties
            
        Returns:
            Created relationship data
        """
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
                CREATE (a)-[r:{relationship_type} $props]->(b)
                RETURN r
                """
                result = session.run(query, from_id=from_node_id, to_id=to_node_id, props=properties or {})
                record = result.single()
                logger.info(f"Added relationship {relationship_type}")
                return dict(record["r"]) if record else None
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return None

    async def extract_nodes_and_edges(self, text: str):
        """Extract entities and relationships from text using LLM."""
        from services.llm_services import llm_service
        import json
        
        prompt = f"""Extract 2-3 key entities and their relationships from this text.
        Text: {text}
        
        Respond with ONLY JSON:
        {{
          "nodes": [ {{"id": "entity_id", "label": "name", "type": "concept|risk|opportunity"}} ],
          "links": [ {{"source": "id1", "target": "id2", "type": "rel_type"}} ]
        }}
        """
        
        try:
            res = await llm_service.call_llm(prompt, temperature=0)
            # Find JSON block
            import re
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        return {"nodes": [], "links": []}


# Global graph service instance
graph_service = GraphService()