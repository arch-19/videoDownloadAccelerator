import requests
import threading
import shutil
import time
import os
import sys
import hashlib

video_url = "https://storage.googleapis.com/vimeo-test/work-at-2.mp4" #Hardcoded url
timeout = 3 #Maximum timeout for response to http request
max_retries = 5 #Maximum number of times a request shoudl be retried on Timeout or connection error
no_of_threads = 12 #Total number of threads
stream_chunk_size = 8192 #chunk size while streaming file content

def download(url, start, this_chunk_size, part, file_name, sess, retry_count):
	try:
		#Get specified range of bytes and write that part of the content to file
		r = sess.get(url,headers={'Range':'bytes=%d-%d' % (start, start + this_chunk_size-1)}, stream=True, timeout=timeout)	
		file_part_name = file_name + '_%d' % part
		print 'Downloading %s' % file_part_name
		with open(file_part_name, 'wb') as f:
			for chunk in r.iter_content(chunk_size=stream_chunk_size):
				if chunk:
					f.write(chunk)

		#Validate if content length and filesize match, else retry download
		if str(os.path.getsize(file_part_name))==r.headers['Content-Length']:
			print ("Downloaded %s" % file_part_name)
		else:
			print "Content length incorrect, download %s incorrect" %file_part_name
			if retry_count<max_retries:
				print "Retry number %d for part %s"%(retry_count+1,part)
				download(video_url, start, this_chunk_size, part, file_name,s,retry_count+1)
	#Retry download in case Timeout or connection error is raised	
	except (requests.exceptions.Timeout,requests.exceptions.ConnectionError) as errc:
		print ("Connection Timeout Error:",errc)
		if retry_count<max_retries:
			time.sleep(2)
			print "Retry number %d for part %s"%(retry_count+1,part)
			download(video_url, start, this_chunk_size, part, file_name,s,retry_count+1)
		else:
			print "Maximum Number of Retries complete. Download Failed"
			return
	#Any other requests error, exit
	except requests.exceptions.RequestException as err:
		print ("Request Exception",err)
		print type(err)
		print "Download %s cannot be completed. Exit"%file_name
		return

#Merge file parts into a single file in order
def mergeFileParts(file_name):
	print "Merging file parts to single file"
	with open(file_name, 'wb') as f:
		for i in range(no_of_threads):
			tmp_file_name = file_name + '_%d' % i
			shutil.copyfileobj(open(tmp_file_name, 'rb'), f)
			os.remove(tmp_file_name)

#Calculate md5 hash value of file and compare with hash value in response header. 
def checkMd5Hash(file_name,hash):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    md5hash = hash.split("md5=")[1]
    encodedhash = (hash_md5.hexdigest().decode("hex").encode("base64")).strip()
    if encodedhash==md5hash:
    	return True
    return False

if __name__ == "__main__":

	file_name = video_url.split("/")[-1]
	#Since we are accessing the same URL, the same TCP connection can be used in the session
	s = requests.Session() 
	r = s.head(video_url,timeout = timeout)
	r.raise_for_status()

	t0 = time.time()
	#If byte range accepted, file is downloaded using multithreading
	if 'Accept-Ranges' in r.headers and r.headers['Accept-Ranges'] == 'bytes':
		size = int(r.headers['content-length']) #Total file size
		
		chunk_size = (size / no_of_threads)
		remainder = (size % no_of_threads)
		threads = []
		#Start threads to download each chunk to file
		for start in range(0, size, chunk_size):
			part = len(threads)
			this_chunk_size = chunk_size if part != no_of_threads-1 else chunk_size + remainder
			t = threading.Thread(target=download, args=(video_url, start, this_chunk_size, part, file_name, s,0))
			threads.append(t)
			t.daemon = True
			t.start()
		#Wait for all threads to complete downloading
		while threading.active_count() > 1:
			time.sleep(0.1)
		t1 = time.time()
		s.close() #close session
		print 'All File parts downloaded.'
		# merge into a single file
		mergeFileParts(file_name)
		print 'Joining complete. File saved in %s' % file_name

	#If byte ranges are not accepted, the file is downloaded with a single stream GET request
	else:
		print "URL does not Accept Ranges\nDownloading %s" %file_name
		with s.get(video_url, stream=True) as resp:
			with open(file_name,'wb') as f:
				for chunk in resp.iter_content(1024*1024):
					if chunk:
						f.write(chunk)
		print '\nDownloaded %s' % file_name	
		t1 = time.time()
	
	total_time = t1-t0
	print "Total Download Time: %d" %total_time #Total time taken to download file
	#validate file integrity by comapring md5 hash value
	if checkMd5Hash(file_name,r.headers["x-goog-hash"]):
		print "Integrity Check Passes. Downloaded File is Validated"
	else:
		print "Integrity Check failed. Downloaded File is Invalid"

	sys.exit()