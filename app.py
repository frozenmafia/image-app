from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from fastapi.responses import FileResponse
import mimetypes
import zipfile
from typing import List
from PIL import Image as PILImage, UnidentifiedImageError
import io
from sqlalchemy.exc import OperationalError
import os

app = FastAPI()

DATABASE_URL = "sqlite:///./image_database.db"

# Define SQLAlchemy models
Base = declarative_base()

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    image_data = Column(LargeBinary)

engine = create_engine(DATABASE_URL)
# Check if database file exists, if not, create it
if not os.path.exists("image_database.db"):

    Base.metadata.create_all(bind=engine)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to save image data to the database
def save_image_to_db(file: UploadFile):
    with SessionLocal() as session:
        # Read the contents of the zip file
        zip_contents = file.file.read()

        # Extract and save each image from the zip file
        with zipfile.ZipFile(io.BytesIO(zip_contents), "r") as zip_ref:
            for filename in zip_ref.namelist():
                # Read the image data
                image_data = zip_ref.read(filename)
                
                # Save the image data to the database
                db_file = Image(filename=filename, image_data=image_data)
                session.add(db_file)

        session.commit()

# Function to check if file is a zip file
def is_zip_file(file: UploadFile):
    content_type, _ = mimetypes.guess_type(file.filename)
    return content_type == "application/zip"

# Upload endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not is_zip_file(file):
            raise HTTPException(status_code=400, detail="Only zip files are allowed")

        save_image_to_db(file)
        return {"message": "Upload successful"}
    except OperationalError as e:
        # If the images table does not exist, create it and try uploading again
        if "no such table: images" in str(e):
            Base.metadata.tables["images"].create(engine)
            return upload_file(file)
        else:
            # Handle other operational errors
            raise HTTPException(status_code=500, detail="Internal server error")

# Other endpoints...


@app.get("/generate_csv")
async def generate_csv():
    with SessionLocal() as session:
        # Query filenames from the database
        images = session.query(Image).all()

        # Generate CSV file content
        csv_content = ""
        for image in images:
            download_url = f"http://localhost:8000/download/{image.filename}"
            csv_content += f"{image.filename},{download_url}\n"

    # Set response headers for downloading the CSV file
    headers = {
        "Content-Disposition": "attachment; filename=image_urls.csv",
        "Content-Type": "text/csv",
    }

    return Response(content=csv_content, media_type="text/csv", headers=headers)


@app.get("/download/{filename}")
async def download_image(filename: str):
    with SessionLocal() as session:
        # Retrieve image from the database based on filename
        image = session.query(Image).filter(Image.filename == filename).first()

        if image is None:
            raise HTTPException(status_code=404, detail="Image not found")

    # Convert the image data to PIL Image
    image_bytes_io = io.BytesIO(image.image_data)
    pil_image = PILImage.open(image_bytes_io)

    # Determine the image format
    image_format = pil_image.format.lower()

    # Convert PIL Image to bytes
    image_bytes_io.seek(0)
    image_bytes = image_bytes_io.getvalue()

    # Return the image data as a response with appropriate content type
    return Response(content=image_bytes, media_type=f"image/{image_format}")



@app.get("/")
async def get_index():
    return FileResponse("index.html")
