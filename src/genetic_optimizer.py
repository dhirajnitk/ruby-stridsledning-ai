import json
import glob
import random
import copy
from agent_backend import load_battlefield_state, CSV_FILE_PATH
from engine import evaluate_threats_advanced, DEFAULT_WEIGHTS
from models import Threat

POPULATION_SIZE = 10
GENERATIONS = 5
MCTS_ITERS_PER_TEST = 50 # Lowered to speed up massive batch testing

WEIGHTS_CACHE = {}

def evaluate_weights(weights_dict, batch_files, base_state):
    """Runs the 100 scenarios with a specific genome and returns a fitness score."""
    # Create a deterministic, hashable key from the weights dictionary
    cache_key = tuple(sorted(weights_dict.items()))
    if cache_key in WEIGHTS_CACHE:
        return WEIGHTS_CACHE[cache_key]
        
    survived = 0
    total_score = 0.0
    
    for file in batch_files:
        with open(file, 'r') as f:
            batch_data = json.load(f)
            
        for scenario_id, threats_data in batch_data.items():
            active_threats = []
            for t in threats_data:
                target_x, target_y = t.get("target_x"), t.get("target_y")
                heading = "Capital X" if (target_x == 418.3 and target_y == 95.0) else "Base"
                active_threats.append(Threat(
                    id=t["id"], x=t["start_x"], y=t["start_y"], speed_kmh=t["speed"],
                    heading=heading, estimated_type=t["type"], threat_value=t["threat_value"]
                ))
                
            # Run the engine using this specific DNA
            decision = evaluate_threats_advanced(base_state, active_threats, mcts_iterations=MCTS_ITERS_PER_TEST, weights=weights_dict)
            score = decision["strategic_consequence_score"]
            
            if score > -100:
                survived += 1
            total_score += score
            
    # Fitness heavily rewards survival rate, then breaks ties using tactical score
    result = ((survived * 1000) + total_score, survived)
    WEIGHTS_CACHE[cache_key] = result
    return result

def mutate(weights):
    """Randomly tweaks a gene by up to +/- 20%."""
    mutated = copy.deepcopy(weights)
    gene = random.choice(list(mutated.keys()))
    mutation_factor = random.uniform(0.8, 1.2)
    mutated[gene] *= mutation_factor
    return mutated

def crossover(parent1, parent2):
    """Mixes genes from two parents."""
    child = {}
    for key in parent1.keys():
        child[key] = parent1[key] if random.random() > 0.5 else parent2[key]
    return child

if __name__ == "__main__":
    print(f"Starting Genetic Algorithm: {POPULATION_SIZE} individuals over {GENERATIONS} generations.")
    base_state = load_battlefield_state(CSV_FILE_PATH)
    batch_files = sorted(glob.glob("simulated_campaign_batch_*.json"))
    
    # Initialize population: The human-engineered default + 9 random mutants
    population = [DEFAULT_WEIGHTS]
    for _ in range(POPULATION_SIZE - 1):
        mutant = copy.deepcopy(DEFAULT_WEIGHTS)
        for key in mutant.keys():
            mutant[key] *= random.uniform(0.5, 1.5)
        population.append(mutant)
        
    for gen in range(GENERATIONS):
        print(f"\n=== GENERATION {gen + 1} ===")
        scored_population = []
        
        for i, ind in enumerate(population):
            fitness, survived = evaluate_weights(ind, batch_files, base_state)
            scored_population.append((fitness, survived, ind))
            print(f" Individual {i+1}: Survived {survived}/100 | Fitness: {fitness:.2f}")
            
        # Sort by fitness descending
        scored_population.sort(key=lambda x: x[0], reverse=True)
        
        best_fitness, best_survived, best_weights = scored_population[0]
        print(f"-> Generation {gen + 1} Best: Survived {best_survived} | Fitness: {best_fitness:.2f}")
        
        # Elitism: Keep the top 2
        next_generation = [scored_population[0][2], scored_population[1][2]]
        
        # Breed the rest
        while len(next_generation) < POPULATION_SIZE:
            # Tournament selection
            p1 = random.choice(scored_population[:5])[2]
            p2 = random.choice(scored_population[:5])[2]
            child = crossover(p1, p2)
            if random.random() < 0.3: # 30% chance to mutate the child
                child = mutate(child)
            next_generation.append(child)
            
        population = next_generation
        
    print("\n=== OPTIMIZATION COMPLETE ===")
    print("Best evolved utility weights:")
    print(json.dumps(best_weights, indent=2))
    
    # Save the best weights to a JSON file so the engine can automatically load them
    out_filepath = "optimized_weights.json"
    with open(out_filepath, "w") as f:
        json.dump(best_weights, f, indent=2)
    print(f"\n[SYSTEM] Successfully saved optimized weights to '{out_filepath}'!")