from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from pytube import YouTube
import json
import os
import pdb
from .models import BlogPost
import assemblyai as aai
import openai

# Create your views here.
@login_required
def index(request):
  return render(request, 'index.html')


def user_login(request):
  if request.method == 'POST':
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
 
    if user is not None:
      login(request, user)
      return render('/')
    else:
      error_message = "User is not found"
      return render(request, 'login.html', {'error_message': error_message})
  return render(request, 'login.html')

def generate_blog(request):
  if request.method == 'POST':
    try:
      data = json.loads(request.body)
      yt_link = data['link']
    except(keyError, json.JSONDecodeError):
      return JsonResponse({'error': 'Invalid data sent'}, status=400)

    title = yt_title(yt_link)

    transcription = get_transcription(yt_link)

    if not transcription:
      return JsonResponse({'error': "Failed to get transcription"}, status=500)

    blog_content = generate_blog_from_transcription(transcription)

    if not blog_content:
      return JsonResponse({'error': 'Failed to generate blog article'}, status=405)

    blog_post = BlogPost.objects.create(
      user = request.user,
      youtube_title = title,
      youtube_link = yt_link,
      generated_content = blog_content
    )
    blog_post.save()

    return JsonResponse({'content': blog_content})
  else:
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def yt_title(link):
  try:
    yt_link = YouTube(link)
    title = yt_link.title
    return title

  except Exception as e:
    print("Error:", e)


def download_audio(link):
  yt = YouTube(link)
  video = yt.streams.filter(only_audio=True).first()
  out_file = video.download(output_path=settings.MEDIA_ROOT)
  base, ext = os.path.splittext(out_file)
  new_file = base + '.mp3'
  os.rename(out_file, new_file)
  return new_file

def get_transcription(link):
  audio_file = download_audio(link)
  aai.settings.api_key = "API_KEY"
  transcriber = aai.Transcriber()
  transcript = transcriber.transcribe(audio_file)

  return transcript.text

def generate_blog_from_transcription(transcription):
    openai.api_key = "Open-AI-API-Key"

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )

    generated_content = response.choices[0].text.strip()

    return generated_content

def user_signup(request):
  if request.method =='POST':
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    repeatPassword = request.POST['repeatPassword']

    if password == repeatPassword:
      try:
        user = User.objects.create_user(username, email, password)
        user.save()
        login(request, user)
        return redirect('/')
      except:
        error_message = 'Error creating account'
        return render(request, 'signup.html', {'error_message': error_message })
    else:
      error_mssage = 'Password is not matching'
      return render(request, 'signup.html', {'error_message': error_message })

  return render(request, 'signup.html')

def user_logout(request):
  logout(request)
  return redirect('/')
