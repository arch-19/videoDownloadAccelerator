# videoDownloadAccelerator
Video Download Accelerator

Approach:
Accept Byte Range 
I decided to use Python for the code challenge, as I am familiar with the requests package and it greatly simplifies using and managing HTTP requests. The documentation is also great. 
I first check whether the server accepts byte range requests. For this I send an intial HEAD request to get only the response headers and no content. If the Response header specifies Accept-Ranges vale as 'bytes', we can send byte ranges in the subsequent requests, else we stream the entire file with a single request. 

I first tested downloading multiple byte ranges and reassembling them into a playable file. As long as the bytes were in order and the filesize remained the same, the file was played correctly. 

Parallel Downloads
To download multple byte ranges in parallel, I considered Python Threading and Multiprocessing modules, and ultimately chose to use multithreading. From many resources online, I learned that threads are light-weight, share the same memory space and are in general preferred for Network and I/O operations. 
To simplify streaming content to open files simultaneously by different threads, I had each thread open a different file and copied the contents of those files to a final file once all the downloads were complete. This also helped ensure that the bytes of each file part would be written in the correct order. 

Integrity Check
Once the file was downloaded, I check for integrity using the MD5 Base64 encoded hash string of the complete file which is available in the 'x-goog-hash' header present in each response. This header is specific to the GoogleCloud API, and is only calculated for the entire file. I calculate the md5 hash of the final file, convert it to Base64 encoded format and compare it to the string present in the response to validate the downloaded file. 
The documentation clearly mentions thaht x-goog-hash values are only created for the complete file and cannot be used to validate individiual byte range requests. While the downloads for each byte range cannot be checked for integrity, we can still validate the content size by comparing the 'Content-Length' header in each byte range response to the downloaded file part. If the file size does not match the content-length header, then the request can be retried.

Error Handling and Retries
HTTP errors are handled by the raise_for_status function of the response object. While downloading file content, the GET request is retried upto 'max_retries' times in case of Connection Errors, Timeout Errors, or if the downloaded file size does not match the size in the header.  

Performance Benchmarks  
I suddenly started facing a drastic increase in total download time since Feb 20th afternoon despite not making any significant changes to my code. I am unsure if it is because of my network, or some throttling by the server because I've been downloading the same file again and again over the past 2 days. I have been trying to diagnose the issue so I can give an accurate measure of performance. For now, my gist has some download times which I had noted before, but it was my intention to test out more chunk sizes and thread counts to reach an optimum value. 

Time Taken to download file	(in seconds)	
Number of threads	  1(Direct Request)	   8		12
Chunk Size			
8192                      220           152         133
16384                     195           145         129
1024*1024                 175           142         124

My expectation was for the time taken to reduce with increase in number of threads and increase in chunk size until a threshold where the overhead from creating and maintaining so many simultaneous downloads starts to decrease the performance.

With more time here are some improvements I would make to the code:-
I would remove the hardcoded variables and implement a command line interface to pass them. 
The Error handling mechanism could also use some improvement to handle different types of exceptions differently, and also make use of python libraries for the purpose of retrying http requests. (for example HTTPAdaptors, urllib3.retry)
Instead of downloading the complete file all over again in case of exceptions, it would also be better to check the existing file_part size and correctly calculate the remaining byte range that needs to be downloaded to complete that chunk. This would save time and improve efficiency.
