import asyncio
from fastapi import FastAPI,APIRouter,HTTPException,BackgroundTasks,Depends
from Backend.database.db_session import get_session
from sqlalchemy.orm import Session
from Backend.database.tables import User
from Backend.utils.security import Security,JWT
from Backend.schemas.requests import RegisterRequest,LoginRequest
from Backend.schemas.responses import RegisterResponse,LoginResponse,UserResponse

router = APIRouter()


@router.post("/register",response_model=RegisterResponse)
def register(request:RegisterRequest,background_tasks:BackgroundTasks,session:Session = Depends(get_session)):
        #checking user existance
        existing_user = (
        session.query(User)
        .filter(User.email == request.email)
        .first()
    )
        if existing_user:
            raise HTTPException(status_code=400,detail="User already exists")
        #Adding New User
        new_user = User(email=request.email,password=Security.hash_password(request.password))
        session.add(new_user)
        session.commit()
        return RegisterResponse(user=UserResponse(id=new_user.id,email=new_user.email),access_token=JWT.create_access_token({"id":new_user.id}),token_type="bearer")
  

@router.post("/login",response_model=LoginResponse)
def login(request:LoginRequest,session:Session = Depends(get_session)):

    user=session.query(User).filter(User.email==request.email).first()
    if not user:
        raise HTTPException(status_code=400,detail="User not found")
    if not Security.verify_password(request.password,user.password):
        raise HTTPException(status_code=400,detail="Incorrect password")
    return LoginResponse(
        user=UserResponse(id=user.id,email=user.email),
        access_token=JWT.create_access_token({"id":user.id}),
        token_type="bearer" 
    )