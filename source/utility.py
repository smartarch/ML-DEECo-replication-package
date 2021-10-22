
def diff(p1,p2,tol=0.001):
    """
        utility function
        calculate the difference between two given values
        if the difference is less than tol (tolerance), then it returns 0
        if p1 < p2 then it returns +1 meaning we must move from p1 to p2
        if p2 > p1 then it returns -1 meaning we must move from p2 to p1
    """
    if abs(p1-p2)<tol:
        return 0
    else:
        if p1<p2:
            return 1
        else:
            return -1