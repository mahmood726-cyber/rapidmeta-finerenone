def cases():
    return [
        {
            "name": "i2_fraction_scale_50_percent",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0.50, "tau2": 0.04, "q": 6.0, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": True,
            "expect_certainty": "MODERATE",
            "why": "This catches reading fractional I-squared 0.50 as 0.50 percent instead of 50 percent.",
        },
        {
            "name": "i2_percent_scale_50_percent",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 50, "tau2": 0.04, "q": 6.0, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": True,
            "expect_certainty": "MODERATE",
            "why": "This catches multiplying an already-percent I-squared value into a spurious two-level inconsistency downgrade.",
        },
        {
            "name": "tau2_zero_with_huge_i2_conflict",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 90, "tau2": 0.0, "q": 30.0, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches silently trusting tau-squared zero when I-squared and Q say heterogeneity is extreme.",
        },
        {
            "name": "i2_zero_with_huge_tau2_conflict",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 10.0, "q": 0.1, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches silently trusting I-squared zero when tau-squared is implausibly large.",
        },
        {
            "name": "transposed_confidence_interval",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 1.10,
                                "ci_low": 1.40,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches accepting a transposed confidence interval where ci_low is greater than ci_high.",
        },
        {
            "name": "rr_interval_crosses_zero",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.50,
                                "ci_low": -0.10,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches accepting an impossible nonpositive lower bound for a ratio-measure confidence interval.",
        },
        {
            "name": "md_uses_zero_null",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.30,
                                "ci_low": -0.20,
                                "ci_high": 0.80,
                                "measure": "MD",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": True,
            "expect_certainty": "MODERATE",
            "why": "This catches using the ratio-measure null of 1 for a mean-difference interval whose null is 0.",
        },
        {
            "name": "rr_uses_one_null",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.90,
                                "ci_low": 0.80,
                                "ci_high": 1.20,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": True,
            "expect_certainty": "MODERATE",
            "why": "This catches using the difference-measure null of 0 for a risk-ratio interval whose null is 1.",
        },
        {
            "name": "k_zero_impossible_pool",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 0,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.0, "df": 0},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches rating a pooled estimate that claims to have zero contributing studies.",
        },
        {
            "name": "k_one_single_study_pool",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 1,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.0, "df": 0},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": True,
            "expect_certainty": "MODERATE",
            "why": "This catches refusing a one-study body just because heterogeneity is structurally not assessable.",
        },
        {
            "name": "negative_k_impossible_pool",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": -1,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.0, "df": -2},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches accepting a negative contributing-study count as a real evidence body.",
        },
        {
            "name": "point_outside_interval",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 1.50,
                                "ci_low": 0.70,
                                "ci_high": 1.20,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches rating a pooled point estimate that lies outside its own confidence interval.",
        },
        {
            "name": "rob_some_concerns_spelling_variants",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {
                        "primary": {
                            "NCT00000001": {"overall": "some concerns"},
                            "NCT00000002": {"overall": "SOME-CONCERNS"},
                            "NCT00000003": {"overall": "Some Concerns"},
                        }
                    },
                },
            },
            "oid": "primary",
            "expect_rated": True,
            "expect_certainty": "MODERATE",
            "why": "This catches treating case and separator variants of SOME CONCERNS as unknown risk-of-bias verdicts.",
        },
        {
            "name": "rob_agreeing_assessor_list_is_final",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {
                        "primary": {
                            "NCT00000001": {
                                "overall": ["LOW", "LOW"],
                                "overall_agreed": False,
                            }
                        }
                    },
                },
            },
            "oid": "primary",
            "expect_rated": True,
            "expect_certainty": "HIGH",
            "why": "This catches refusing a two-assessor risk-of-bias list where both assessors reached the same verdict.",
        },
        {
            "name": "rob_disagreeing_assessor_list_is_pending",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {
                        "primary": {
                            "NCT00000001": {
                                "overall": ["LOW", "HIGH"],
                                "overall_agreed": False,
                            }
                        }
                    },
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches issuing a certainty rating from an unadjudicated two-assessor risk-of-bias disagreement.",
        },
        {
            "name": "withdrawn_pool_with_stored_certainty",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                                "withdrawn": True,
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "certainty": "HIGH",
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                },
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches displaying or preserving a certainty grade for a withdrawn pooled estimate.",
        },
        {
            "name": "empty_measure_refuses_null",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches guessing a line of no effect when the summary-measure string is empty.",
        },
        {
            "name": "none_measure_refuses_null",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 4,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": None,
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 3},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches guessing a line of no effect when the summary-measure value is None.",
        },
        {
            "name": "k_ten_without_publication_bias_test",
            "object": {
                "results": {
                    "by_outcome": {
                        "primary": {
                            "k": 10,
                            "pooled": {
                                "point": 0.70,
                                "ci_low": 0.60,
                                "ci_high": 0.80,
                                "measure": "RR",
                            },
                            "heterogeneity": {"i2": 0, "tau2": 0.0, "q": 0.2, "df": 9},
                            "grade": {
                                "indirectness": {
                                    "state": "NO_DOWNGRADE",
                                    "levels": 0,
                                    "reason": "Synthetic directness judgement.",
                                }
                            },
                        }
                    }
                },
                "risk_of_bias": {
                    "tool": "RoB 2",
                    "by_outcome": {"primary": {"NCT00000001": {"overall": "LOW"}}},
                },
            },
            "oid": "primary",
            "expect_rated": False,
            "expect_certainty": None,
            "why": "This catches treating publication bias as not assessable at k equals 10 when an asymmetry test is now required.",
        },
    ]


if __name__ == "__main__":
    print(len(cases()))
