# Two coherent pools for sglt2-hf, each over ONE endpoint definition. Verbatim output.
#
# The four trials do NOT share one endpoint, so the k=4 pool is withdrawn and stays withdrawn.
# What remains is TWO separate questions, each internally coherent:
#
#   A. TWO-COMPONENT  -- cardiovascular death or hospitalisation for heart failure.
#      DAPA-HF contributes its SECONDARY (the 2-component composite); EMPEROR-Reduced and
#      EMPEROR-Preserved contribute their PRIMARY. k = 3.
#
#   B. THREE-COMPONENT -- cardiovascular death, hospitalisation for heart failure, OR an
#      urgent heart-failure visit. DAPA-HF and DELIVER contribute their PRIMARY. k = 2.
#      EMPEROR-Reduced and EMPEROR-Preserved register no urgent-visit endpoint at any rank,
#      so they cannot join this one.
#
# DELIVER contributes to A not at all -- it registers no two-component composite at any of its
# seven ranks. That is why A is k=3 and not k=4, and it is established by reading every rank
# rather than by matching the primary.
#
# Inputs are the per-trial hazard ratios and 95% intervals already stored on the object, each
# read from its trial's own reported analysis. Nothing is recomputed from counts here.

library(metafor)

fit <- function(label, nct, hr, lo, hi) {
  yi  <- log(hr)
  sei <- (log(hi) - log(lo)) / (2 * qnorm(0.975))
  cat("\n", strrep("=", 78), "\n", label, "\n", strrep("=", 78), "\n", sep = "")
  cat("trials:", paste(nct, collapse = ", "), "\n\n")
  res <- rma(yi = yi, sei = sei, method = "REML", slab = nct)
  print(res)
  cat("\nBack-transformed to the hazard-ratio scale:\n")
  pred <- predict(res, transf = exp)
  print(pred)
  invisible(res)
}

cat("R environment, quoted rather than asserted:\n")
cat(R.version.string, "\n")
cat("metafor", as.character(packageVersion("metafor")), "\n")

# --- A. TWO-COMPONENT, k = 3 -------------------------------------------------------------
fit("A. CARDIOVASCULAR DEATH OR HOSPITALISATION FOR HEART FAILURE (two-component), k=3",
    c("NCT03036124 DAPA-HF (secondary)",
      "NCT03057977 EMPEROR-Reduced (primary)",
      "NCT03057951 EMPEROR-Preserved (primary)"),
    hr = c(0.75, 0.75, 0.79),
    lo = c(0.65, 0.65, 0.69),
    hi = c(0.85, 0.86, 0.90))

# --- B. THREE-COMPONENT, k = 2 -----------------------------------------------------------
fit("B. CV DEATH, HOSPITALISATION FOR HF, OR URGENT HF VISIT (three-component), k=2",
    c("NCT03036124 DAPA-HF (primary)",
      "NCT03619213 DELIVER (primary)"),
    hr = c(0.74, 0.82),
    lo = c(0.65, 0.73),
    hi = c(0.85, 0.92))

cat("\n", strrep("=", 78), "\n", sep = "")
cat("The two pools are NOT alternatives and neither supersedes the other.\n")
cat("They estimate the effect on DIFFERENT COMPOSITE ENDPOINTS, and the k=4 pool that\n")
cat("mixed them remains withdrawn.\n")
