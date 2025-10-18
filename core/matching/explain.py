def why_this(listing_vec, taste, top_k=3):
    """
    Calculates the contribution of each feature to the listing's score
    and returns the top K as explainability chips.
    """
    contribs = []
    # Check numeric features
    for k,v in listing_vec["num"].items():
        contribs.append((k, v * taste["num"].get(k,0)))
    
    # Check tag features
    for t,v in listing_vec["tags"].items():
        if v>0:
            # Tags are boolean (1 or 0), so contribution is just the taste weight
            contribs.append((t, taste["tags"].get(t,0)))
            
    # Sort by the absolute value of the contribution (magnitude)
    contribs.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # Format the top K contributions for display (e.g., "+kitchen finishes" or "-train noise")
    return [f"{k} ({'+' if s>=0 else ''}{s:.2f})" for k,s in contribs[:top_k]]