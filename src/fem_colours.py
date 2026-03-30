# FEM brand colour palette
# Warm terracotta -> brown -> taupe -> steel -> navy
FEM_ORANGE = "#C1693A"
FEM_BROWN  = "#8B5E45"
FEM_TAUPE  = "#7A7068"
FEM_STEEL  = "#5A6E7F"
FEM_NAVY   = "#2E3F52"

# Ordered palette for charts (5 colours)
FEM_PALETTE = [FEM_ORANGE, FEM_BROWN, FEM_TAUPE, FEM_STEEL, FEM_NAVY]

# Priority colours using FEM palette
PRIORITY_COLORS = {
    "Very high": FEM_ORANGE,
    "High":      FEM_BROWN,
    "Medium":    FEM_STEEL,
    "Low":       FEM_TAUPE,
}

FEM_SCALE = [
    [0.0,  "#f8f3ee"],
    [0.25, "#e8c4a8"],
    [0.5,  FEM_ORANGE],
    [0.75, FEM_BROWN],
    [1.0,  FEM_NAVY],
]