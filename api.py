from flask import Flask, request, jsonify
from flask_cors import CORS

from src.analysis.trend_detector import detect_trends
from src.analysis.signal_analyzer import extract_signals_from_results
from src.research.web_search import search_web
from src.analysis.opportunity_scorer import score_opportunities
from src.analysis.creative_generator import generate_creative_directions
from src.visualization.visual_prompt_generator import generate_visual_prompts
from src.visualization.trend_visual_generator import generate_trend_visual_prompts
from src.visualization.image_generator import generate_image

import hashlib
import uuid
import json


app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "AROHA API"})


@app.route("/api/research", methods=["POST"])
def research():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body is required."}), 400

        query = data.get("query", "").strip()
        pipeline_mode = data.get("pipeline_mode", "full")
        generate_images = data.get("generate_images", False)

        if not query:
            return jsonify({"status": "error", "message": "Research query is required."}), 400

        # Every research request gets a unique visual run ID. Generated images
        # from older sessions are never silently reused as current output.
        run_id = uuid.uuid4().hex[:12]

        print("\n" + "=" * 70)
        print("AROHA RESEARCH STARTED")
        print("=" * 70)
        print(f"Query: {query}")
        print("\n[1/3] Searching the web...")

        results = search_web(query, max_results=5)
        print(f"Web research completed: {len(results) if results else 0} results")

        print("\n[2/3] Extracting signals...")
        signals = extract_signals_from_results(results)
        print(f"Signals extracted: {len(signals) if signals else 0}")

        print("\n[3/3] Detecting trends...")
        trends = detect_trends(signals)
        print(f"Trends detected: {len(trends) if trends else 0}")

        opportunities = []
        creative_directions = []
        visual_prompts = []
        generated_images = []
        trend_visual_prompts = []
        trend_images = []

        if pipeline_mode == "trends_only":
            print("\n[4/4] Generating trend visualizations...")
            try:
                trend_visual_prompts = generate_trend_visual_prompts(trends)
                for index, visual in enumerate(trend_visual_prompts, start=1):
                    if not isinstance(visual, dict):
                        continue
                    prompt = visual.get("visual_prompt") or visual.get("prompt")
                    if not prompt:
                        continue
                    try:
                        image_path = generate_image(prompt=prompt, filename=f"{run_id}_trend_{index}.webp")
                        trend_images.append({"name": visual.get("name", f"Emerging pattern {index}"), "image_path": image_path, "visual_rationale": visual.get("visual_rationale", ""), "image_source": "flux_current_run", "run_id": run_id})
                    except Exception as image_error:
                        print(f"Trend image {index} failed: {image_error}")
            except Exception as trend_error:
                print(f"Trend visual generation failed: {trend_error}")

        if pipeline_mode != "trends_only":
            print("\n[4/7] Scoring opportunities...")
            opportunities = score_opportunities(trends)
            print(f"Opportunities generated: {len(opportunities) if opportunities else 0}")

            print("\n[5/7] Generating creative directions...")
            creative_directions = generate_creative_directions(opportunities)
            print(f"Creative directions generated: {len(creative_directions) if creative_directions else 0}")

            print("\n[6/7] Generating visual prompts...")
            visual_prompts = generate_visual_prompts(creative_directions)
            print(f"Visual prompts generated: {len(visual_prompts) if visual_prompts else 0}")

            print("\n[7/7] Image generation...")
            if generate_images:
                for index, visual in enumerate(visual_prompts):
                    if not isinstance(visual, dict):
                        continue
                    visual_prompt = visual.get("visual_prompt")
                    if not visual_prompt:
                        continue
                    try:
                        image_path = generate_image(
                            prompt=visual_prompt,
                            filename=f"concept_{index + 1}.webp",
                        )
                        generated_images.append({
                            "name": visual.get("name", f"Concept {index + 1}"),
                            "image_path": image_path,
                        })
                    except Exception as image_error:
                        print(f"Image generation failed for concept {index + 1}: {image_error}")
        else:
            print("\n[4-7] Stopped after trends — waiting for user direction.")

        response_data = {
            "status": "success",
            "run_id": run_id,
            "query": query,
            "pipeline_mode": pipeline_mode,
            "results": results,
            "signals": signals,
            "trends": trends,
            "opportunities": opportunities,
            "creative_directions": creative_directions,
            "visual_prompts": visual_prompts,
            "generated_images": generated_images,
            "trend_visual_prompts": trend_visual_prompts,
            "trend_images": trend_images,
        }

        print("\n" + "=" * 70)
        print("AROHA RESEARCH COMPLETED")
        print("=" * 70 + "\n")
        return jsonify(response_data), 200

    except Exception as error:
        import traceback
        print("\n" + "=" * 70)
        print("AROHA BACKEND ERROR")
        print("=" * 70)
        traceback.print_exc()
        print("=" * 70 + "\n")
        return jsonify({
            "status": "error",
            "message": str(error),
            "error_type": type(error).__name__,
        }), 500


@app.route("/api/opportunities", methods=["POST"])
def opportunities_api():
    try:
        data = request.get_json() or {}
        trends = data.get("trends", [])
        if not isinstance(trends, list) or not trends:
            return jsonify({"status": "error", "message": "Trends are required."}), 400
        opportunities = score_opportunities(trends)
        return jsonify({"status": "success", "opportunities": opportunities}), 200
    except Exception as error:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(error), "error_type": type(error).__name__}), 500


@app.route("/api/creative", methods=["POST"])
def creative_api():
    """
    Generate the complete creative package for one selected opportunity:
    creative directions -> visual prompts -> FLUX images.

    This keeps the user decision-driven flow intact: AROHA waits for an
    opportunity selection before spending tokens/time on creative work.
    """
    try:
        data = request.get_json() or {}
        selected_opportunity = data.get("selected_opportunity")
        if not isinstance(selected_opportunity, dict):
            opportunities = data.get("opportunities", [])
            if isinstance(opportunities, list) and opportunities and isinstance(opportunities[0], dict):
                selected_opportunity = opportunities[0]

        if not isinstance(selected_opportunity, dict):
            return jsonify({
                "status": "error",
                "message": "A single selected opportunity is required."
            }), 400

        # The ID is derived only from the selected opportunity. This makes each
        # opportunity an independent creative workspace and prevents stale state.
        opportunity_key = json.dumps(selected_opportunity, sort_keys=True, ensure_ascii=False)
        opportunity_id = hashlib.sha1(opportunity_key.encode("utf-8")).hexdigest()[:12]

        print(f"\n[CREATIVE] Selected opportunity: {opportunity_id}")
        print("[CREATIVE] Generating creative directions...")
        creative_directions = generate_creative_directions([selected_opportunity])

        if not isinstance(creative_directions, list):
            creative_directions = []

        print(f"[CREATIVE] Directions generated: {len(creative_directions)}")

        print("[CREATIVE] Generating visual prompts...")
        visual_prompts = generate_visual_prompts(creative_directions)

        if not isinstance(visual_prompts, list):
            visual_prompts = []

        print(f"[CREATIVE] Visual prompts generated: {len(visual_prompts)}")

        generated_images = []
        image_errors = []

        print("[CREATIVE] Generating FLUX images...")
        for index, visual in enumerate(visual_prompts, start=1):
            if not isinstance(visual, dict):
                continue

            visual_prompt = visual.get("visual_prompt") or visual.get("prompt")
            if not visual_prompt:
                image_errors.append({
                    "concept": index,
                    "error": "Visual prompt was empty."
                })
                continue

            try:
                image_path = generate_image(
                    prompt=visual_prompt,
                    filename=f"{opportunity_id}_{uuid.uuid4().hex[:8]}_concept_{index}.webp",
                )

                generated_images.append({
                    "name": visual.get("name", f"Concept {index}"),
                    "image_path": image_path,
                    "visual_prompt": visual_prompt,
                    "image_source": "flux_current_run",
                    "run_id": opportunity_id,
                })

                print(f"[CREATIVE] FLUX image {index} generated: {image_path}")

            except Exception as image_error:
                print(f"[CREATIVE] FLUX image {index} failed: {image_error}")
                image_errors.append({
                    "concept": index,
                    "name": visual.get("name", f"Concept {index}"),
                    "error": str(image_error),
                })

        package_status = "complete" if generated_images else ("strategy_only" if creative_directions else "failed")

        return jsonify({
            "status": "success" if creative_directions else "error",
            "package_status": package_status,
            "opportunity_id": opportunity_id,
            "selected_opportunity": selected_opportunity,
            "visual_generation": {
                "status": "generated" if generated_images else "unavailable",
                "current_run_only": True,
            },
            "creative_directions": creative_directions,
            "visual_prompts": visual_prompts,
            "generated_images": generated_images,
            "image_errors": image_errors,
        }), 200 if creative_directions else 500

    except Exception as error:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(error),
            "error_type": type(error).__name__
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
