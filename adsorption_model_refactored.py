# adsorption_model_refactored.py
# =========================================================
# Refactored Adsorbent Evaluation Model
# - Dictionary-based structure
# - Easy adsorbent addition
# - Environmental condition control
# - Ranking system
# - Reusable evaluation engine
# =========================================================

import numpy as np
import matplotlib.pyplot as plt

# =========================================================
# 1. DATABASE
# =========================================================

adsorbent_data = {

    "Corn BA700": {
        "petroleum": 67.29,
        "diesel": np.nan,
        "mb": np.nan,
        "iodine": np.nan
    },

    "Bagasse ASCB400": {
        "petroleum": 67.30,
        "diesel": np.nan,
        "mb": np.nan,
        "iodine": np.nan
    },

    "Sawdust": {
        "petroleum": np.nan,
        "diesel": 98.0,
        "mb": np.nan,
        "iodine": np.nan
    },

    "Plastic AC": {
        "petroleum": np.nan,
        "diesel": np.nan,
        "mb": 220,
        "iodine": 1084
    },

    "Commercial AC": {
        "petroleum": np.nan,
        "diesel": np.nan,
        "mb": 290.66,
        "iodine": np.nan
    }
}

# =========================================================
# 2. WEIGHTS
# =========================================================

weights = {
    "petroleum": 0.35,
    "diesel": 0.15,
    "mb": 0.30,
    "iodine": 0.20
}

# =========================================================
# 3. NORMALIZATION
# =========================================================

def normalize_property(data_dict, property_name):

    values = []

    for ads in data_dict:
        values.append(data_dict[ads][property_name])

    arr = np.array(values, dtype=float)

    if np.all(np.isnan(arr)):
        return arr

    max_val = np.nanmax(arr)

    return (arr / max_val) * 100


# =========================================================
# 4. ENVIRONMENTAL MODEL
# =========================================================

def alpha_neutral(pH):
    return 1 / (1 + 10**(6.0 - pH))


def surface_factor(pH):
    return 1 - 0.01 * (pH - 7)**2


def temp_factor(T):
    return 1 - 0.005 * (T - 25)


def pH_correction(pH, adsorbent):

    if adsorbent == "Corn BA700":
        return np.exp(-((pH-8)**2)/(2*1.0**2)) * 0.3 + 0.8

    elif adsorbent == "Bagasse ASCB400":
        return np.exp(-((pH-8.5)**2)/(2*0.8**2)) * 0.25 + 0.85

    elif adsorbent == "Commercial AC":
        return np.exp(-((pH-8)**2)/(2*0.7**2)) * 0.4 + 0.7

    else:
        return np.exp(-((pH-7)**2)/(2*1.2**2)) * 0.2 + 0.9


# =========================================================
# 5. SCORE ENGINE
# =========================================================

def calculate_scores(data_dict, weights):

    # Normalize each property
    petroleum_n = normalize_property(data_dict, "petroleum")
    diesel_n = normalize_property(data_dict, "diesel")
    mb_n = normalize_property(data_dict, "mb")
    iodine_n = normalize_property(data_dict, "iodine")

    adsorbents = list(data_dict.keys())

    results = {}

    for i, ads in enumerate(adsorbents):

        values = {
            "petroleum": petroleum_n[i],
            "diesel": diesel_n[i],
            "mb": mb_n[i],
            "iodine": iodine_n[i]
        }

        total_score = 0
        count = 0

        for key in values:

            if not np.isnan(values[key]):
                total_score += weights[key] * values[key]
                count += 1

        potential = total_score

        # Confidence penalty
        confidence = 0.75 + 0.25 * (count / 4)

        conservative = potential * confidence

        results[ads] = {
            "potential": potential,
            "conservative": conservative,
            "confidence": confidence
        }

    return results


# =========================================================
# 6. ENVIRONMENTAL APPLICATION
# =========================================================

def apply_environment(results, pH=7, T=25):

    final_results = {}

    for ads in results:

        env_factor = (
            alpha_neutral(pH)
            * surface_factor(pH)
            * temp_factor(T)
            * pH_correction(pH, ads)
        )

        final_potential = results[ads]["potential"] * env_factor
        final_conservative = results[ads]["conservative"] * env_factor

        final_results[ads] = {
            "potential": final_potential,
            "conservative": final_conservative,
            "confidence": results[ads]["confidence"],
            "env_factor": env_factor
        }

    return final_results


# =========================================================
# 7. RANKING SYSTEM
# =========================================================

def rank_adsorbents(final_results):

    ranking = sorted(
        final_results.items(),
        key=lambda x: x[1]["conservative"],
        reverse=True
    )

    return ranking


# =========================================================
# 8. PERFORMANCE GRADE
# =========================================================

def performance_grade(score):

    if score >= 35:
        return "Excellent"

    elif score >= 25:
        return "Competitive"

    elif score >= 15:
        return "Moderate"

    else:
        return "Weak"


# =========================================================
# 9. PRINT RESULTS
# =========================================================

def print_results(final_results):

    ranking = rank_adsorbents(final_results)

    print("\n=================================================")
    print("FINAL ADSORBENT PERFORMANCE RANKING")
    print("=================================================\n")

    for rank, (ads, values) in enumerate(ranking, start=1):

        grade = performance_grade(values["conservative"])

        print(f"#{rank} {ads}")
        print(f"Potential Score     : {values['potential']:.2f}")
        print(f"Conservative Score  : {values['conservative']:.2f}")
        print(f"Confidence          : {values['confidence']:.2f}")
        print(f"Environmental Factor: {values['env_factor']:.4f}")
        print(f"Performance Grade   : {grade}")
        print("-------------------------------------------------")


# =========================================================
# 10. ADD NEW ADSORBENT
# =========================================================

def add_adsorbent(
    data_dict,
    name,
    petroleum=np.nan,
    diesel=np.nan,
    mb=np.nan,
    iodine=np.nan
):

    data_dict[name] = {
        "petroleum": petroleum,
        "diesel": diesel,
        "mb": mb,
        "iodine": iodine
    }


# =========================================================
# 11. VISUALIZATION
# =========================================================

def plot_ranking(final_results):
    ranking = rank_adsorbents(final_results)

    names = [r[0] for r in ranking]
    scores = [r[1]["conservative"] for r in ranking]

    # 권장 방식: plt.subplots()로 figure와 ax 생성
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(names, scores)

    ax.set_ylabel("Conservative Efficiency")
    ax.set_title("Adsorbent Ranking")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20)

    for i, v in enumerate(scores):
        ax.text(i, v + 0.3, f"{v:.1f}", ha='center')

    fig.tight_layout()
    return fig   # plt.show() 대신 fig 반환


# =========================================================
# 12. MAIN EXECUTION
# =========================================================

if __name__ == "__main__":

    # -----------------------------------------------------
    # Environmental Conditions
    # -----------------------------------------------------

    pH = 7
    T = 25

    # -----------------------------------------------------
    # Calculate
    # -----------------------------------------------------

    base_results = calculate_scores(adsorbent_data, weights)

    final_results = apply_environment(
        base_results,
        pH=pH,
        T=T
    )

    # -----------------------------------------------------
    # Output
    # -----------------------------------------------------

    print_results(final_results)

    # -----------------------------------------------------
    # Visualization
    # -----------------------------------------------------

    plot_ranking(final_results)