import requests
import os

def test_mentor_registration_with_video():
    # API endpoint
    url = 'http://localhost:8000/api/users/register/mentor/'
    
    # Test video file path (create a small test file)
    test_video_path = 'samplementor.mp4'
    with open(test_video_path, 'wb') as f:
        f.write(b'test video content')
    
    try:
        # Prepare form data
        data = {
            'email': 'test_mentor_api2@example.com',
            'first_name': 'Test',
            'last_name': 'Mentor API',
            'title': 'Dr.',
            'job_title': 'Professor',
            'institutional_affiliation': 'Test University',
            'nationality': 'Test Country',
            'city': 'Test City',
            'bio': 'This is a test mentor account created via API',
        }
        
        # Open the file
        files = {
            'mentor_intro_video': ('samplementor.mp4', open(test_video_path, 'rb'), 'video/mp4')
        }
        
        # Make the POST request
        response = requests.post(url, data=data, files=files)
        
        # Print response
        print(f'Status code: {response.status_code}')
        print(f'Response: {response.text}')
        
        # Check if successful
        if response.status_code == 201:
            print('Mentor registration with video successful!')
        else:
            print('Mentor registration failed.')
            
    except Exception as e:
        print(f'Error: {e}')
    finally:
        # Clean up the test file
        if os.path.exists(test_video_path):
            os.remove(test_video_path)
        
        # Close any open file handles
        for file_obj in files.values():
            if hasattr(file_obj[1], 'close'):
                file_obj[1].close()

if __name__ == '__main__':
    test_mentor_registration_with_video()