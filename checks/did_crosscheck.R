# Cross-check of the Python Callaway-Sant'Anna estimator against the R `did` package
# on the single simulated panel. Writes results/did_crosscheck.csv.
suppressPackageStartupMessages({ library(did) })

panel <- read.csv("results/panel.csv")
py <- read.csv("results/event_study.csv")

gt <- att_gt(yname = "y", tname = "t", idname = "id", gname = "G", data = panel,
             control_group = "nevertreated", base_period = "varying",
             est_method = "reg", bstrap = FALSE, cband = FALSE)
dyn <- aggte(gt, type = "dynamic", min_e = -6, max_e = 8, na.rm = TRUE, bstrap = FALSE)

r <- data.frame(e = dyn$egt, did_estimate = dyn$att.egt, did_se = dyn$se.egt)
out <- merge(r, py[, c("e", "cs", "cs_se")], by = "e")
out$abs_diff <- abs(out$did_estimate - out$cs)
write.csv(out, "results/did_crosscheck.csv", row.names = FALSE)
cat(sprintf("did %s: max |ATT(e) difference| = %.2e over %d event times\n",
            packageVersion("did"), max(out$abs_diff), nrow(out)))
