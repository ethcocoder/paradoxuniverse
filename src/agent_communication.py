import time
from typing import List, Dict, Any, Optional
from src.entity import Agent
from src.world import World
from src.agent_social import AgentSocial
from src.agent_meta import AgentMeta

class AgentCommunication:
    """
    Handles message passing and cognitive map updates.
    """
    
    @staticmethod
    def broadcast(world: World, sender: Agent, receivers: List[Agent], payload: Dict[str, Any], msg_type: str = "MAP_UPDATE"):
        """
        Sends a message from sender to receivers.
        """
        message = {
            "sender_id": sender.id,
            "tick": sender.last_tick_updated,
            "type": msg_type,
            "payload": payload # Partial map or specific info
        }
        
        for receiver in receivers:
             if receiver.id != sender.id:
                 receiver.message_queue.append(message)

    @staticmethod
    def process_messages(agent: Agent) -> int:
        """
        Processes all messages in the queue and updates cognitive map.
        Returns number of messages processed.
        """
        count = len(agent.message_queue)
        for msg in agent.message_queue:
            sender_id = msg.get("sender_id")
            payload = msg.get("payload", {})
            
            # Phase 13: Handle ALARM
            msg_type = msg.get("type", "MAP_UPDATE")
            if msg_type == "ALARM":
                hazard_loc = payload.get("location_id")
                # Trust Check (Phase 13)
                trust = agent.trust_scores.get(sender_id, AgentSocial.INITIAL_TRUST)
                if trust >= AgentSocial.INITIAL_TRUST and hazard_loc:
                    # Believe them! Avoid this location. 
                    # Apply a massive penalty to reflection score
                    AgentMeta.update_score(agent, hazard_loc, -2.0)
            
            # Phase 15: Handle HELP_CALL
            elif msg_type == "HELP_CALL":
                loc = payload.get("location_id")
                trust = agent.trust_scores.get(sender_id, AgentSocial.INITIAL_TRUST)
                if trust >= AgentSocial.INITIAL_TRUST and loc:
                    # Update map to know food is there
                    if loc not in agent.cognitive_map:
                         agent.cognitive_map[loc] = {"neighbors": [], "objects": []}
                    if "COOP_FOOD" not in agent.cognitive_map[loc]["objects"]:
                         agent.cognitive_map[loc]["objects"].append("COOP_FOOD")
                    
                    # Phase 16: Remember who requested help
                    agent.cognitive_map[loc]["requester_id"] = sender_id
                    
                    # Also boost reflection score to encourage going there
                    AgentMeta.update_score(agent, loc, 1.0)
            
            # Phase 17: Handle STORY
            elif msg_type == "STORY":
                # Payload is a Story dict: {topic, location, tick, source, veracity}
                topic = payload.get("topic")
                loc = payload.get("location")
                trust = agent.trust_scores.get(sender_id, AgentSocial.INITIAL_TRUST)
                
                # Epistemic Trust: Do we believe this story?
                if trust >= 0.5:
                    # Integrate Knowledge
                    if topic == "HAZARD":
                        # Mark location as dangerous in Meta
                        AgentMeta.update_score(agent, loc, -1.5) # Strong penalty
                        # Update map if possible (add 'HAZARD' tag if not present)
                        if loc not in agent.cognitive_map:
                             agent.cognitive_map[loc] = {"neighbors": [], "objects": []}
                        if "HAZARD" not in agent.cognitive_map[loc]["objects"]:
                             agent.cognitive_map[loc]["objects"].append("HAZARD")
                             
                    elif topic == "FOOD":
                        # Mark location as good
                        AgentMeta.update_score(agent, loc, 0.5)
                        if loc not in agent.cognitive_map:
                             agent.cognitive_map[loc] = {"neighbors": [], "objects": []}
                        if "FOOD" not in agent.cognitive_map[loc]["objects"]:
                             agent.cognitive_map[loc]["objects"].append("FOOD")

                    # Retain story as Hearsay (prevent loops? check if we have it)
                    # We accept it as our own truth to retell
                    # But maybe track original source?
                    payload["source"] = sender_id # Mark that we heard it from them
                    agent.stories.append(payload)
            
            # Phase 6/11: Social - Calculate Trust Reward
            if sender_id and msg_type == "MAP_UPDATE":
                trust_boost = 0.05
                # Phase 11: Reward high-value info (Food discovery)
                for loc_id, info in payload.items():
                    if isinstance(info, dict):
                        objs = info.get("objects", [])
                        if "FOOD" in objs or "ObjectType.FOOD" in objs:
                            known_objs = agent.cognitive_map.get(loc_id, {}).get("objects", [])
                            if "FOOD" not in known_objs:
                                trust_boost += 0.15 # Extra boost for revealing food
                
                AgentSocial.record_interaction(agent, sender_id, trust_boost)
            
            # Map merging logic (Only if type is MAP_UPDATE)
            if msg_type == "MAP_UPDATE":
                AgentCommunication._merge_map(agent, payload)
        
        agent.message_queue.clear()
        return count

    @staticmethod
    def _merge_map(agent: Agent, new_data: Dict[str, Dict[str, Any]]):
        """
        Merges external map data into agent's cognitive map.
        Strategy: Additive merge. Unknown locations are added.
        Known locations are updated if info seems richer (e.g. has objects).
        """
        for loc_id, info in new_data.items():
            if loc_id not in agent.cognitive_map:
                agent.cognitive_map[loc_id] = info
            else:
                # Merge logic
                # For now, simplistic: Union of neighbors
                current = agent.cognitive_map[loc_id]
                
                # Update neighbors
                new_neighbors = info.get("neighbors", [])
                if new_neighbors:
                    current_neighbors = set(current.get("neighbors", []))
                    current_neighbors.update(new_neighbors)
                    current["neighbors"] = list(current_neighbors)
                
                # Update objects (overwrite if present in update)
                # Note: This is imperfect (what if object removed?), but consistent with "sharing what I see"
                if "objects" in info:
                    current["objects"] = info["objects"]
