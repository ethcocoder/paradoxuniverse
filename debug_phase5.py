from src.sim import Simulation
from src.entity import Agent, Object, ObjectType

sim = Simulation(seed=123)
sim.world.add_location('A', ['B'])
sim.world.add_location('B', ['A', 'C'])
sim.world.add_location('C', ['B'])

food = Object(type=ObjectType.FOOD, value=10, location_id='C')
sim.world.add_entity(food)

agent = Agent(location_id='A')
agent.cognitive_map = {
    'A': {'neighbors': ['B']},
    'B': {'neighbors': ['A', 'C']},
    'C': {'neighbors': ['B'], 'objects': ['FOOD']}
}
sim.world.add_entity(agent)

print("="*60)
print("SETUP DIAGNOSTICS:")
print(f"Food ID: {food.id}, Location: {food.location_id}")
print(f"Food in entities: {food.id in sim.world.entities}")
print(f"Location C objects list: {sim.world.locations.get('C', {}).get('objects', [])}")
print(f"Objects at C: {sim.world.get_objects_at('C')}")
print("="*60)


print("="*60)
for i in range(3):  # Changed to 3 ticks to match test
    print(f"\n--- BEFORE TICK {i} ---")
    print(f"Location: {agent.location_id}, Energy: {agent.energy}, Goal: {agent.current_goal}")
    print(f"Plan queue: {[f'{p.type.name}->{p.target_id}' for p in agent.plan_queue]}")
    food_at_c = [o for o in sim.world.get_objects_at('C') if o.type == ObjectType.FOOD]
    print(f"Food at C: {len(food_at_c)} items")
    
    sim.tick()
    
    print(f"AFTER TICK {i}: {agent.last_action}")

print("\n" + "="*60)
print(f"FINAL CHECK:")
print(f"  Agent location: {agent.location_id} (expected: 'C')")
print(f"  Agent energy: {agent.energy}")
food_remaining = [o for o in sim.world.entities.values() if hasattr(o, 'type') and o.type == ObjectType.FOOD]
print(f"  Food remaining: {len(food_remaining)} (expected: 0)")
print(f"\nTest Result: {'PASS' if agent.location_id == 'C' and len(food_remaining) == 0 else 'FAIL'}")

