from loguru import logger
from typing import List, Dict, Optional
from services.llm_services import llm_service


class RedTeamService:
    """
    Red Team Agent Service - Dedicated to finding flaws, risks, and breaking consensus.
    
    This agent's ONLY job is to:
    - Attack assumptions
    - Find every way the plan could fail
    - Challenge groupthink
    - Expose blind spots
    """
    
    def __init__(self):
        logger.info("🔴 Red Team Service initialized")
    
    async def attack_assumptions(
        self,
        topic: str,
        plan: str,
        assumptions: List[str]
    ) -> Dict:
        """
        Systematically attack every assumption in the plan.
        
        Args:
            topic: Discussion topic
            plan: The proposed plan/consensus
            assumptions: List of assumptions to attack
            
        Returns:
            Analysis of assumption vulnerabilities
        """
        assumptions_text = "\n".join([f"{i+1}. {a}" for i, a in enumerate(assumptions)])
        
        prompt = f"""You are a RED TEAM AGENT. Your job is to ruthlessly attack assumptions.

Topic: {topic}

Proposed Plan:
{plan}

Assumptions Made:
{assumptions_text}

For EACH assumption, provide:
1. Why it might be WRONG
2. Evidence that contradicts it
3. What happens if it's false
4. Alternative assumption

Respond in JSON format:
{{
  "assumptions_attacked": [
    {{
      "assumption": "original assumption",
      "why_wrong": "reasoning",
      "contradicting_evidence": "evidence",
      "impact_if_false": "consequences",
      "alternative": "better assumption",
      "confidence_score": 0-100 (how likely assumption is wrong)
    }}
  ],
  "most_dangerous_assumption": "the riskiest assumption",
  "overall_plan_viability": 0-100
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a ruthless Red Team analyst. Find every flaw. No mercy.",
                temperature=0.7,
                max_tokens=1000
            )
            
            if result:
                import json
                import re
                
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
            
            return {"error": "Failed to generate attack analysis"}
            
        except Exception as e:
            logger.error(f"Error in assumption attack: {e}")
            return {"error": str(e)}
    
    async def find_failure_modes(
        self,
        topic: str,
        plan: str
    ) -> Dict:
        """
        Find every possible way the plan could fail.
        
        Args:
            topic: Discussion topic
            plan: The proposed plan
            
        Returns:
            Comprehensive failure mode analysis
        """
        prompt = f"""You are a RED TEAM AGENT specializing in failure mode analysis.

Topic: {topic}

Plan to Destroy:
{plan}

Identify ALL possible failure modes:
1. Market failures
2. Technical failures
3. Financial failures
4. Competitive failures
5. Regulatory failures
6. Execution failures
7. Black swan events

For each failure mode:
- How likely is it? (0-100%)
- How severe is the impact? (0-100%)
- Early warning signs
- Mitigation strategy (if any)

Respond in JSON:
{{
  "failure_modes": [
    {{
      "category": "market|technical|financial|competitive|regulatory|execution|black_swan",
      "scenario": "what goes wrong",
      "probability": 0-100,
      "severity": 0-100,
      "risk_score": 0-100,
      "warning_signs": ["sign1", "sign2"],
      "mitigation": "how to prevent or reduce impact"
    }}
  ],
  "critical_failure": "most dangerous failure mode",
  "plan_survivability": 0-100
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a pessimistic analyst. Expect everything to go wrong.",
                temperature=0.6,
                max_tokens=1200
            )
            
            if result:
                import json
                import re
                
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
            
            return {"error": "Failed to generate failure analysis"}
            
        except Exception as e:
            logger.error(f"Error in failure mode analysis: {e}")
            return {"error": str(e)}
    
    async def break_consensus(
        self,
        topic: str,
        consensus: str,
        agent_opinions: List[Dict]
    ) -> Dict:
        """
        Break the consensus by finding blind spots and groupthink.
        
        Args:
            topic: Discussion topic
            consensus: The agreed-upon consensus
            agent_opinions: List of agent opinions that formed consensus
            
        Returns:
            Analysis of consensus weaknesses
        """
        opinions_text = "\n".join([
            f"{op.get('agent_role', 'Unknown')}: {op.get('content', '')}"
            for op in agent_opinions
        ])
        
        prompt = f"""You are a RED TEAM AGENT. Your mission: BREAK THE CONSENSUS.

Topic: {topic}

Consensus Reached:
{consensus}

Agent Opinions:
{opinions_text}

Attack the consensus:
1. What is EVERYONE missing?
2. Where is the GROUPTHINK?
3. What uncomfortable truths are being ignored?
4. What would a contrarian expert say?
5. What historical examples contradict this consensus?

Be BRUTALLY honest. Respond in JSON:
{{
  "consensus_weaknesses": [
    {{
      "weakness": "what's wrong",
      "evidence": "supporting facts",
      "ignored_perspective": "what's being missed",
      "severity": "low|medium|high|critical"
    }}
  ],
  "groupthink_indicators": ["indicator1", "indicator2"],
  "contrarian_viewpoint": "what the opposition would say",
  "historical_precedents": ["example1", "example2"],
  "should_proceed": true/false,
  "recommendation": "go|no-go|proceed-with-extreme-caution"
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a contrarian. Challenge everything. Break consensus.",
                temperature=0.8,
                max_tokens=1000
            )
            
            if result:
                import json
                import re
                
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
            
            return {"error": "Failed to break consensus"}
            
        except Exception as e:
            logger.error(f"Error in consensus breaking: {e}")
            return {"error": str(e)}
    
    async def full_red_team_analysis(
        self,
        topic: str,
        plan: str,
        consensus: Dict,
        agent_opinions: List[Dict],
        assumptions: Optional[List[str]] = None
    ) -> Dict:
        """
        Complete Red Team analysis combining all attacks.
        
        Args:
            topic: Discussion topic
            plan: The proposed plan
            consensus: Consensus data from simulation
            agent_opinions: All agent opinions
            assumptions: Optional list of assumptions
            
        Returns:
            Comprehensive Red Team report
        """
        logger.info(f"🔴 Starting full Red Team analysis on: {topic}")
        
        # Run all analyses in parallel
        import asyncio
        
        tasks = [
            self.find_failure_modes(topic, plan)
        ]
        
        if assumptions:
            tasks.append(self.attack_assumptions(topic, plan, assumptions))
        
        if consensus:
            tasks.append(self.break_consensus(
                topic,
                consensus.get("consensus", ""),
                agent_opinions
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile report
        report = {
            "topic": topic,
            "plan_analyzed": plan,
            "failure_modes": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
            "assumptions_attacked": results[1] if len(results) > 1 and not isinstance(results[1], Exception) else None,
            "consensus_broken": results[2] if len(results) > 2 and not isinstance(results[2], Exception) else None,
            "red_team_verdict": "PROCEED" if not results else "RECONSIDER",
            "critical_risks": [],
            "recommendations": []
        }
        
        # Extract critical risks
        if "failure_modes" in report["failure_modes"]:
            critical = [
                fm for fm in report["failure_modes"]["failure_modes"]
                if fm.get("risk_score", 0) > 70
            ]
            report["critical_risks"] = critical
        
        # Generate overall recommendation
        risk_count = len(report["critical_risks"])
        if risk_count >= 3:
            report["red_team_verdict"] = "DO NOT PROCEED - Too many critical risks"
        elif risk_count >= 1:
            report["red_team_verdict"] = "PROCEED WITH EXTREME CAUTION"
        
        report["recommendations"] = [
            "Address all critical risks before proceeding",
            "Create contingency plans for top 3 failure modes",
            "Reassess assumptions quarterly",
            "Assign risk owners for each failure mode"
        ]
        
        logger.info(f"🔴 Red Team analysis complete. Verdict: {report['red_team_verdict']}")
        return report


# Global Red Team service instance
red_team_service = RedTeamService()
