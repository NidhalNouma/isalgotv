FROM public.ecr.aws/lambda/python:3.9 

COPY lambda_handler.py ${LAMBDA_TASK_ROOT}  

CMD ["lambda_handler.handler"]  
