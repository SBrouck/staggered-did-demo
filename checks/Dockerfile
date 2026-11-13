# R environment for the cross-check against the reference `did` package.
# rocker/r-ver pins CRAN to a dated Posit Package Manager snapshot (fixed versions);
# linux/amd64 is used because the snapshot serves prebuilt binaries for it.
FROM --platform=linux/amd64 rocker/r-ver:4.4.1
RUN install2.r --error --skipinstalled did
