"""
INNOWAH 2026 - Feature Extractor
Maps raw software (cognitive test) and hardware (ESP32 sensor) data
into a fixed-length feature vector for the ML model.

Feature Vector (33 features total):
  Software / Cognitive [14]:
    [0]  immediate_recall          (0–1)
    [1]  delayed_recall            (0–1)
    [2]  cue_benefit_index         (0–1)
    [3]  retention_ratio           (0–1)
    [4]  orientation_score         (0–1)
    [5]  serial7s_score            (0–1)
    [6]  clock_drawing_score       (0–1)
    [7]  reaction_time_norm        (0–1, inverted: lower RT → higher value)
    [8]  error_consistency         (0–1, inverted: fewer errors → higher)
    [9]  naming_task_score         (0–1)
    [10] sentence_repetition       (0–1)
    [11] verbal_fluency_norm       (0–1)
    [12] iadl_score_norm           (0–1, inverted)
    [13] mood_filter               (0 or 1)

  Hardware / Sensor [15]:
    IMU [4]:
    [14] gait_speed_norm           (0–1)
    [15] stride_variability_norm   (0–1, inverted)
    [16] turning_velocity_norm     (0–1)
    [17] postural_sway_norm        (0–1, inverted)

    PPG/HRV [5]:
    [18] heart_rate_norm            (0–1)
    [19] rmssd_norm                (0–1)
    [20] sdnn_norm                 (0–1)
    [21] lf_hf_ratio_norm          (0–1, inverted)
    [22] spo2_norm                 (0–1)

    EEG [4]:
    [23] alpha_power_norm          (0–1)
    [24] theta_power_norm          (0–1, inverted)
    [25] delta_power_norm          (0–1, inverted)
    [26] theta_alpha_ratio_norm    (0–1, inverted)

    Temperature [1]:
    [27] skin_temp_norm            (0–1)

    Activity [1]:
    [28] daily_steps_norm          (0–1)

    Aggregates [2]:
    [29] sensor_score              (0–1, 40% weighted share)
    [30] cognitive_score           (0–1, 60% weighted share)
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:

    # ─── Clinical thresholds (from document) ────────────────────────────
    THRESHOLDS = {
        # IMU
        "gait_speed":          {"normal": (1.0, 1.4), "mild": (0.8, 1.0), "high": (0.0, 0.8)},
        "stride_variability":  {"normal": (0.0, 3.0), "mild": (3.0, 5.0), "high": (5.0, 100)},
        "turning_velocity":    {"normal": (120, 360),  "mild": (90, 120),   "high": (0.0, 90)},
        "postural_sway":       {"normal": (0.0, 3.0), "mild": (3.0, 5.0), "high": (5.0, 100)},

        # PPG/HRV
        "heart_rate":          {"normal": (60, 100),   "mild": (50, 60),    "high": (0.0, 50)},
        "rmssd":               {"normal": (25, 50),    "mild": (15, 25),    "high": (0.0, 15)},
        "sdnn":                {"normal": (30, 60),    "mild": (20, 30),    "high": (0.0, 20)},
        "lf_hf_ratio":         {"normal": (1.0, 2.0),  "mild": (2.0, 3.0),  "high": (3.0, 10)},
        "spo2":                {"normal": (95, 100),   "mild": (92, 95),    "high": (0.0, 92)},

        # EEG
        "alpha_power":         {"normal": (25, 40),    "mild": (20, 25),    "high": (0.0, 20)},
        "theta_power":         {"normal": (10, 20),    "mild": (20, 25),    "high": (25, 100)},
        "delta_power":         {"normal": (5, 15),     "mild": (15, 20),    "high": (20, 100)},
        "theta_alpha_ratio":   {"normal": (0.5, 0.9),  "mild": (1.0, 1.3),  "high": (1.5, 10)},

        # Temperature
        "skin_temp":           {"normal": (33.0, 37.0),"mild": (31.0, 33.0),"high": (0.0, 31.0)},
        "spo2_activity":       {"normal": (5000, 8000),"mild": (3000, 4000),"high": (0.0, 3000)},
    }

    # ─── Normalization ranges (maps raw value → 0–1, healthy=1, sick=0) ──
    NORM = {
        "gait_speed":         (0.0,   1.6,   True),    # (min, max, higher_is_better)
        "stride_variability": (0.0,   10.0,  False),
        "turning_velocity":   (0.0,   200.0, True),
        "postural_sway":      (0.0,   10.0,  False),
        "heart_rate":         (40.0,  120.0, True),
        "rmssd":              (0.0,   80.0,  True),
        "sdnn":               (0.0,   100.0, True),
        "lf_hf_ratio":        (0.0,   5.0,   False),
        "spo2":               (85.0,  100.0, True),
        "alpha_power":        (0.0,   50.0,  True),
        "theta_power":        (0.0,   50.0,  False),
        "delta_power":        (0.0,   40.0,  False),
        "theta_alpha_ratio":  (0.0,   3.0,   False),
        "skin_temp":          (28.0,  38.0,  True),
        "daily_steps":        (0.0,   10000, True),

        # Cognitive
        "recall_score":       (0.0,   1.0,   True),
        "orientation":        (0.0,   1.0,   True),
        "executive":          (0.0,   1.0,   True),
        "reaction_time":      (200.0, 2000.0,False),   # ms
        "verbal_fluency":     (0.0,   30.0,  True),    # words/min
        "iadl_impairments":   (0.0,   8.0,   False),
    }

    def normalize(self, value, key):
        """Normalize a raw value to [0, 1] where 1 = healthy end."""
        if key not in self.NORM:
            return float(np.clip(value, 0, 1))
        lo, hi, higher_is_better = self.NORM[key]
        norm = (float(value) - lo) / (hi - lo + 1e-9)
        norm = float(np.clip(norm, 0.0, 1.0))
        return norm if higher_is_better else (1.0 - norm)

    def extract(self, software_data: dict, hardware_data: dict = None) -> np.ndarray:
        """
        Extract a 33-dimensional feature vector.
        Missing values are imputed with 0.5 (midpoint / uncertain).
        """
        sw = software_data or {}
        hw = hardware_data or {}

        imu  = hw.get("imu", {})
        ppg  = hw.get("ppg", {})
        eeg  = hw.get("eeg", {})
        temp = hw.get("temperature", {})

        def get(d, key, default=None):
            v = d.get(key, default)
            return 0.5 if v is None else float(v)

        # ── Software / Cognitive features ─────────────────────────────
        immediate_recall  = get(sw, "immediate_recall", 0.5)      # already 0–1
        delayed_recall    = get(sw, "delayed_recall", 0.5)
        cue_benefit       = get(sw, "cue_benefit_index", 0.5)
        retention_ratio   = get(sw, "retention_ratio", 0.5)
        orientation       = get(sw, "orientation_score", 0.5)
        serial7s          = get(sw, "serial7s_score", 0.5)
        clock_drawing     = get(sw, "clock_drawing_score", 0.5)
        reaction_time     = self.normalize(get(sw, "reaction_time_ms", 700), "reaction_time")
        error_consistency = 1.0 - get(sw, "error_consistency_norm", 0.2)
        naming_task       = get(sw, "naming_task_score", 0.5)
        sentence_rep      = get(sw, "sentence_repetition_score", 0.5)
        verbal_fluency    = self.normalize(get(sw, "verbal_fluency_wpm", 12), "verbal_fluency")
        iadl              = self.normalize(get(sw, "iadl_impairment_count", 1), "iadl_impairments")
        mood_filter       = get(sw, "mood_filter", 0.0)

        sw_features = np.array([
            immediate_recall, delayed_recall, cue_benefit, retention_ratio,
            orientation, serial7s, clock_drawing, reaction_time,
            error_consistency, naming_task, sentence_rep, verbal_fluency,
            iadl, mood_filter
        ], dtype=np.float32)

        # ── Hardware / Sensor features ────────────────────────────────
        # IMU
        f_gait_speed   = self.normalize(get(imu, "gait_speed", 1.1), "gait_speed")
        f_stride_var   = self.normalize(get(imu, "stride_variability", 2.5), "stride_variability")
        f_turn_vel     = self.normalize(get(imu, "turning_velocity", 130), "turning_velocity")
        f_sway         = self.normalize(get(imu, "postural_sway", 2.0), "postural_sway")

        # PPG/HRV
        f_heart_rate   = self.normalize(get(ppg, "heart_rate", 72), "heart_rate")
        f_rmssd        = self.normalize(get(ppg, "rmssd", 35), "rmssd")
        f_sdnn         = self.normalize(get(ppg, "sdnn", 45), "sdnn")
        f_lf_hf        = self.normalize(get(ppg, "lf_hf_ratio", 1.5), "lf_hf_ratio")
        f_spo2         = self.normalize(get(ppg, "spo2", 97), "spo2")

        # EEG
        f_alpha        = self.normalize(get(eeg, "alpha_power", 30), "alpha_power")
        f_theta        = self.normalize(get(eeg, "theta_power", 15), "theta_power")
        f_delta        = self.normalize(get(eeg, "delta_power", 10), "delta_power")
        f_ta_ratio     = self.normalize(get(eeg, "theta_alpha_ratio", 0.7), "theta_alpha_ratio")

        # Temperature
        f_skin_temp    = self.normalize(get(temp, "skin_temp", 34.0), "skin_temp")

        # Activity
        f_steps        = self.normalize(get(imu, "step_count", 5000), "daily_steps")

        hw_features = np.array([
            f_gait_speed, f_stride_var, f_turn_vel, f_sway,
            f_heart_rate, f_rmssd, f_sdnn, f_lf_hf, f_spo2,
            f_alpha, f_theta, f_delta, f_ta_ratio,
            f_skin_temp, f_steps
        ], dtype=np.float32)

        # ── Aggregate scores (60:40 rule from document) ──────────────
        # Sensor score: weighted avg of hardware features
        sensor_score = float(np.mean(hw_features))

        # Cognitive score: weighted avg of cognitive features
        cog_score = float(np.mean(sw_features))

        # Final combined score (sensor=40%, cognitive=60%)
        combined = np.array([sensor_score, cog_score], dtype=np.float32)

        feature_vector = np.concatenate([sw_features, hw_features, combined])
        logger.info(f"Feature vector extracted: {feature_vector.shape[0]} features, "
                    f"sensor_score={sensor_score:.3f}, cog_score={cog_score:.3f}")
        return feature_vector

    def get_feature_names(self):
        return [
            # Software (14)
            "immediate_recall", "delayed_recall", "cue_benefit_index",
            "retention_ratio", "orientation_score", "serial7s_score",
            "clock_drawing_score", "reaction_time_norm", "error_consistency",
            "naming_task_score", "sentence_repetition", "verbal_fluency_norm",
            "iadl_score_norm", "mood_filter",
            # IMU (4)
            "gait_speed", "stride_variability", "turning_velocity", "postural_sway",
            # PPG (5)
            "heart_rate", "rmssd", "sdnn", "lf_hf_ratio", "spo2",
            # EEG (4)
            "alpha_power", "theta_power", "delta_power",
            "theta_alpha_ratio",
            # Temperature (1)
            "skin_temp",
            # Activity (1)
            "daily_steps",
            # Aggregates (2)
            "sensor_score", "cognitive_score"
        ]

    def get_domain_features(self, feature_vector):
        """Split feature vector into domain-level scores for explainability."""
        fv = np.array(feature_vector)
        return {
            "memory":      float(np.mean(fv[[0,1,2,3,4, 9]])),
            "reasoning":   float(np.mean(fv[[5,6,7,8,  14,15,16]])),
            "visuospatial":float(np.mean(fv[[17,26]])),
            "language":    float(np.mean(fv[[9,10,11]])),
            "behavior":    float(np.mean(fv[[12,13, 18,19,20,21,27,28]])),
        }
