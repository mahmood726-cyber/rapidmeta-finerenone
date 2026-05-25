# Install metafor to a user-writable library.
user_lib <- file.path(Sys.getenv("APPDATA"), "R-libs")
if (!dir.exists(user_lib)) dir.create(user_lib, recursive = TRUE)
.libPaths(c(user_lib, .libPaths()))
install.packages("metafor", repos = "https://cloud.r-project.org",
                 lib = user_lib, quiet = TRUE)
cat("metafor install:", "metafor" %in% rownames(installed.packages()), "\n")
cat("lib path:", user_lib, "\n")
