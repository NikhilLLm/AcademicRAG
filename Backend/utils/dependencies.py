from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from Backend.database.db_session import get_session
from Backend.database.tables import User
from Backend.utils.security import JWT


def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Usage in routes:
        @router.get("/endpoint")
        def my_endpoint(current_user: User = Depends(get_current_user)):
            # current_user is now available
            pass
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Missing or invalid Authorization header"
        )
    
    # Extract token
    token = auth_header.split(" ")[1]
    
    # Verify and decode token
    payload = JWT.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or expired token"
        )
    
    # Get user from database
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token payload"
        )
    
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="User not found"
        )
    
    return user


def get_optional_user(request: Request, session: Session = Depends(get_session)) -> User | None:
    """
    Get user if authenticated, else return None.
    Does NOT raise generic 401/404 errors.
    """

    try:
        user = get_current_user(request, session)
        return user
    except HTTPException as e:
        return None
