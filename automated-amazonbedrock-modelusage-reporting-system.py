import json
import boto3,io,csv,gzip
import datetime,ast
from datetime import datetime
import time,traceback
import pandas as pd
import os.path
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def lambda_handler(event, context):
    try:

        def convertToMil(value):
            dt_obj = datetime.strptime(str(value),'%Y-%m-%d %H:%M:%S')
            result = int(dt_obj.timestamp() * 1000)
            return result
            
        def get_s3_bucket_key(s3_path):
            path_parts=s3_path.replace("s3://","").split("/")
            s3_bucket=path_parts.pop(0)
            s3_key="/".join(path_parts)
            return s3_bucket, s3_key
        
        s3_client = boto3.client('s3')
        cloudwatch_client = boto3.client('logs')
        # Specify the bucket name and object key
        bucket_name = 'demo_bucket'
        object_key = 'sample_model_price.csv'
        models_price_obj = s3_client.get_object(Bucket = bucket_name, Key = object_key)
        models_price_lines = models_price_obj['Body'].read().decode('utf-8').split('\n')
        fieldnames = models_price_lines[0].replace('"','').split(',')
        tmp_list = [row for row in csv.DictReader(models_price_lines[1:], fieldnames)]
        models_price_list = json.loads(json.dumps([row for row in tmp_list]))
        # last 24 hr in millisecond
        time_millisec = 86400000 
        currentdateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        getCurrentMilsec = convertToMil(str(currentdateTime))
        getYesterdayMilsec = getCurrentMilsec - time_millisec
        
        # https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html
        bedrockmodelusage_query = "fields @timestamp,@message"

        queryString_list = [bedrockmodelusage_query]
        final_data = []
        
        for queryString in queryString_list:
            # The below code queries the cloudwatch log group where the Amazon bedrock log datas are stored.
            response = cloudwatch_client.start_query(
                logGroupName= "demo/bedrock/logs",
                startTime=getYesterdayMilsec,
                endTime=getCurrentMilsec,
                queryString=queryString
            )
            data = json.dumps(response, indent=2)
            jsonResult = json.loads(data)
            time.sleep(5)
            queryResponse = cloudwatch_client.get_query_results(queryId=jsonResult['queryId'])
            queryResponsedata = json.dumps(queryResponse, indent=2)
            queryResponsejsonResult = json.loads(queryResponsedata)

            #Account Id, Identity ARN, Model Id, Region Name, Number of Input tokens, Number of output tokens, number of images generated, Charges incurred
            # the below code snippet is to parse the response and do usage charge calculation
            for each_result_list in reversed(queryResponsejsonResult["results"]):
                for each_result_json in each_result_list:
                    
                    if each_result_json["field"] == "@message" and "modelId" in each_result_json["value"]:
                        each_field_value = json.loads(each_result_json["value"])
                        account_id = each_field_value['accountId']
                        identity_arn =  each_field_value['identity']['arn']
                        model_id = each_field_value['modelId'].split("/")[-1]
                        region_name = each_field_value['region']
                        input_tokens_count= 0
                        output_tokens_count=0
                        image_count=0
                        charges = 0
                        if model_id == "anthropic.claude-3-opus-20240229-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            claude_opus_price_dict = models_price_list[12]
                            inputTokenPrice = float(claude_opus_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(claude_opus_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                        elif model_id == "anthropic.claude-3-sonnet-20240229-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            claude_sonnet_price_dict = models_price_list[13]
                            inputTokenPrice = float(claude_sonnet_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(claude_sonnet_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "anthropic.claude-3-haiku-20240307-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            claude_haiku_price_dict = models_price_list[14]
                            inputTokenPrice = float(claude_haiku_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(claude_haiku_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "anthropic.claude-v2:1" and "input" in each_field_value and "output" in each_field_value:
                            claude_21_price_dict = models_price_list[11]
                            inputTokenPrice = float(claude_21_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(claude_21_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "anthropic.claude-v2" and "input" in each_field_value and "output" in each_field_value:
                            claude_v2_price_dict = models_price_list[10]
                            inputTokenPrice = float(claude_v2_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(claude_v2_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "anthropic.claude-instant-v1" and "input" in each_field_value and "output" in each_field_value:
                            claude_instant_price_dict = models_price_list[9]
                            inputTokenPrice = float(claude_instant_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(claude_instant_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "ai21.j2-ultra-v1" and "input" in each_field_value and "output" in each_field_value:
                            ai21_ultra_price_dict = models_price_list[1]
                            inputTokenPrice = float(ai21_ultra_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(ai21_ultra_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "ai21.j2-mid-v1" and "input" in each_field_value and "output" in each_field_value:
                            ai21_mid_price_dict = models_price_list[0]
                            inputTokenPrice = float(ai21_mid_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(ai21_mid_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "cohere.command-r-plus-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            command_r_plus_price_dict = models_price_list[17]
                            inputTokenPrice = float(command_r_plus_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(command_r_plus_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "cohere.command-r-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            command_r_price_dict = models_price_list[18]
                            inputTokenPrice = float(command_r_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(command_r_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "cohere.command-text-v14" and "input" in each_field_value and "output" in each_field_value:
                            command_text_price_dict = models_price_list[15]
                            inputTokenPrice = float(command_text_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(command_text_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "cohere.command-light-text-v14" and "input" in each_field_value and "output" in each_field_value:
                            command_text_lite_price_dict = models_price_list[16]
                            inputTokenPrice = float(command_text_lite_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(command_text_lite_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "meta.llama3-8b-instruct-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            llama3_8b_price_dict = models_price_list[21]
                            inputTokenPrice = float(llama3_8b_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(llama3_8b_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "meta.llama3-70b-instruct-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            llama3_70b_price_dict = models_price_list[22]
                            inputTokenPrice = float(llama3_70b_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(llama3_70b_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "meta.llama2-13b-chat-v1" and "input" in each_field_value and "output" in each_field_value:
                            llama2_13b_price_dict = models_price_list[23]
                            inputTokenPrice = float(llama2_13b_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(llama2_13b_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "meta.llama2-70b-chat-v1" and "input" in each_field_value and "output" in each_field_value:
                            llama2_70b_price_dict = models_price_list[24]
                            inputTokenPrice = float(llama2_70b_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(llama2_70b_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "mistral.mistral-7b-instruct-v0:2" and "input" in each_field_value and "output" in each_field_value:
                            mistral_7b_price_dict = models_price_list[25]
                            inputTokenPrice = float(mistral_7b_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(mistral_7b_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "mistral.mixtral-8x7b-instruct-v0:1" and "input" in each_field_value and "output" in each_field_value:
                            mistral_87b_price_dict = models_price_list[26]
                            inputTokenPrice = float(mistral_87b_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(mistral_87b_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "mistral.mistral-large-2402-v1:0" and "input" in each_field_value and "output" in each_field_value:
                            mistral_large_price_dict = models_price_list[27]
                            inputTokenPrice = float(mistral_large_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(mistral_large_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "amazon.titan-text-lite-v1" and "input" in each_field_value and "output" in each_field_value:
                            titan_lite_price_dict = models_price_list[2]
                            inputTokenPrice = float(titan_lite_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(titan_lite_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "amazon.titan-text-express-v1" and "input" in each_field_value and "output" in each_field_value:
                            titan_express_price_dict = models_price_list[3]
                            inputTokenPrice = float(titan_express_price_dict["inputTokenPrice"].strip())
                            outputTokenPrice = float(titan_express_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            output_tokens_count=each_field_value["output"]["outputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) +(float(output_tokens_count/1000)*outputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "amazon.titan-embed-text-v1" and "input" in each_field_value:
                            titan_embed_v1_price_dict = models_price_list[4]
                            inputTokenPrice = float(titan_embed_v1_price_dict["inputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "amazon.titan-embed-text-v2:0" and "input" in each_field_value:
                            titan_emb_v2_price_dict = models_price_list[5]
                            inputTokenPrice = float(titan_emb_v2_price_dict["inputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) 
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "amazon.titan-embed-image-v1" and "input" in each_field_value:
                            titan_emb_image_price_dict = models_price_list[8]
                            inputTokenPrice = float(titan_emb_image_price_dict["inputTokenPrice"].strip())
                            inputImagePrice = float(titan_emb_image_price_dict["outputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            if input_tokens_count == 0 and "inputBodyS3Path" in each_field_value["input"]:
                                charges = inputImagePrice
                                image_count = 1
                            elif input_tokens_count > 0 and "inputBodyS3Path" in each_field_value["input"]:
                                charges = (float(input_tokens_count/1000)*inputTokenPrice) + inputImagePrice
                                image_count = 1
                            elif input_tokens_count > 0 :
                                charges = (float(input_tokens_count/1000)*inputTokenPrice)
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "cohere.embed-english-v3" and "input" in each_field_value:
                            cohere_emb_price_dict = models_price_list[19]
                            inputTokenPrice = float(cohere_emb_price_dict["inputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) 
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "cohere.embed-multilingual-v3" and "input" in each_field_value:
                            coher_emb_multi_price_dict = models_price_list[20]
                            inputTokenPrice = float(coher_emb_multi_price_dict["inputTokenPrice"].strip())
                            input_tokens_count= each_field_value["input"]["inputTokenCount"]
                            charges = (float(input_tokens_count/1000)*inputTokenPrice) 
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "amazon.titan-image-generator-v1" and "input" in each_field_value:
                            titan_image_512_price_dict = models_price_list[6]
                            standard_512_image_price = float(titan_image_512_price_dict["inputTokenPrice"].strip())
                            premium_512_image_price = float(titan_image_512_price_dict["outputTokenPrice"].strip())
                            titan_image_1024_price_dict = models_price_list[7]
                            standard_1024_image_price = float(titan_image_1024_price_dict["inputTokenPrice"].strip())
                            premium_1024_image_price = float(titan_image_1024_price_dict["outputTokenPrice"].strip())
                            image_height_width_dict = {"1024x1024":["1024x1024","768x1152","1152x768","768x1280","1280x768",
                            "896x1152","1152x896","768x1408","1408x768","640x1408","1408x640","1152x640","1173x640"],
                            "512x512":["768x768","512x512","384x576","576x384","384x640","640x384","448x576","576x448",
                            "384x704","704x384","320x704","704x320"]}
                            
                            default_quality = "standard"
                            default_image_count = 1
                            default_height = "1408"
                            default_width = "1408"
                            default_pricing_resolution = "1024x1024"
                            if "inputBodyS3Path" in each_field_value["input"]:
                                s3_path = each_field_value["input"]["inputBodyS3Path"]
                                bucket_name,object_key= get_s3_bucket_key(s3_path)
                                s3log_obj = s3_client.get_object(Bucket = bucket_name, Key = object_key)
                                buf = io.BytesIO(s3log_obj['Body'].read()) # reads whole gz file into memory
                                for each_json_log in gzip.GzipFile(fileobj=buf):
                                    required_json_log = json.loads(each_json_log)
                                    if "imageGenerationConfig" in required_json_log:
                                        if "quality" in required_json_log['imageGenerationConfig']:
                                            default_quality = required_json_log['imageGenerationConfig']["quality"]
                                        if "numberOfImages" in required_json_log['imageGenerationConfig']:
                                            default_image_count = required_json_log['imageGenerationConfig']["numberOfImages"]
                                        if "height" in required_json_log['imageGenerationConfig']:
                                            default_height = str(required_json_log['imageGenerationConfig']["height"])
                                        if "width" in required_json_log['imageGenerationConfig']:
                                            default_width = str(required_json_log['imageGenerationConfig']["width"])
                                        if default_height+'x'+default_width in image_height_width_dict["1024x1024"]:
                                            default_pricing_resolution = "1024x1024"
                                        elif default_height+'x'+default_width in image_height_width_dict["512x512"]:
                                            default_pricing_resolution = "512x512"
                                        if default_pricing_resolution == "1024x1024" and default_quality == "standard":
                                            charges= standard_1024_image_price * default_image_count
                                        elif default_pricing_resolution == "512x512" and default_quality == "standard":
                                            charges= standard_512_image_price * default_image_count
                                        elif default_pricing_resolution == "1024x1024" and default_quality == "premium":
                                            charges= premium_1024_image_price * default_image_count
                                        elif default_pricing_resolution == "512x512" and default_quality == "premium":
                                            charges= premium_512_image_price * default_image_count
                                    else:
                                        # all default configurations will be applied
                                        charges= standard_1024_image_price
                            elif "inputBodyJson" in each_field_value["input"]:
                                if 'imageGenerationConfig' in each_field_value["input"]["inputBodyJson"]:
                                    if "quality" in each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']:
                                        default_quality = each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']["quality"]
                                    if "numberOfImages" in each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']:
                                        default_image_count = each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']["numberOfImages"]
                                    if "height" in each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']:
                                        default_height = str(each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']["height"])
                                    if "width" in each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']:
                                        default_width = str(each_field_value["input"]["inputBodyJson"]['imageGenerationConfig']["width"])
                                    if default_height+'x'+default_width in image_height_width_dict["1024x1024"]:
                                        default_pricing_resolution = "1024x1024"
                                    elif default_height+'x'+default_width in image_height_width_dict["512x512"]:
                                        default_pricing_resolution = "512x512"
                                    if default_pricing_resolution == "1024x1024" and default_quality == "standard":
                                        charges= standard_1024_image_price * default_image_count
                                    elif default_pricing_resolution == "512x512" and default_quality == "standard":
                                        charges= standard_512_image_price * default_image_count
                                    elif default_pricing_resolution == "1024x1024" and default_quality == "premium":
                                        charges= premium_1024_image_price * default_image_count
                                    elif default_pricing_resolution == "512x512" and default_quality == "premium":
                                        charges= premium_512_image_price * default_image_count
                                else:
                                    # all default configurations will be applied
                                    charges= standard_1024_image_price
                            image_count = default_image_count
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        elif model_id == "stability.stable-diffusion-xl-v1":
                            stable_price_dict = models_price_list[28]
                            less_than_50step_price = float(stable_price_dict["inputTokenPrice"].strip())
                            greater_than_50step_price =  float(stable_price_dict["outputTokenPrice"].strip())
                            default_steps = 30
                            default_image_count = 1
                            if "inputBodyS3Path" in each_field_value["input"]:
                                s3_path = each_field_value["input"]["inputBodyS3Path"]
                                bucket_name,object_key= get_s3_bucket_key(s3_path)
                                s3log_obj = s3_client.get_object(Bucket = bucket_name, Key = object_key)
                                buf = io.BytesIO(s3log_obj['Body'].read()) # reads whole gz file into memory
                                for each_json_log in gzip.GzipFile(fileobj=buf):
                                    required_json_log = json.loads(each_json_log)
                                if "steps" in required_json_log:
                                     default_steps = required_json_log["steps"]
                            elif "inputBodyJson" in each_field_value["input"]:
                                if "steps" in each_field_value["input"]["inputBodyJson"]:
                                    default_steps = each_field_value["input"]["inputBodyJson"]["steps"]
                            if default_steps <= 50:
                                charges = less_than_50step_price
                            else:
                                charges = greater_than_50step_price
                            image_count = default_image_count
                            #print([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        if charges > 0:
                            final_data.append([account_id,identity_arn,model_id,region_name,input_tokens_count,output_tokens_count,image_count,charges])
                        

                
        
        # The final data is written to excel file
        final_df = pd.DataFrame(final_data,columns=['Account_ID','Identity_ARN','Model_ID','Region_Name',"Input_token_count","Output_token_count",'Image_count',"Charges_incurred"])
        TMP_FILE_NAME = '/tmp/'+ "AmazonBedrock_Charges_last_24hr_each_Model_"+ str(getCurrentMilsec)+".csv"
        final_df.to_csv(TMP_FILE_NAME, index = False)
        s3_client.upload_file(Filename=TMP_FILE_NAME, Bucket=bucket_name, Key="AmazonBedrock_Charges_last_24hr_each_Model/AmazonBedrock_Charges_last_24hr_each_Model_"+ str(getCurrentMilsec)+".csv")
        # The below code snippet is to send email. It uses Amazon SES service.
        SENDER = "test@gmail.com"
        RECIPIENTS = ["test@gmail.com"]
        AWS_REGION = "us-west-2"
        SUBJECT = "Amazon bedrock charges incurred details for each model invocations for last 24hr data"
        BODY_TEXT = "Amazon bedrock charges incurred details for each model invocations for last 24hr data is attached with this mail for reference."
        ses_client = boto3.client('ses',region_name=AWS_REGION)
        msg = MIMEMultipart()
        msg['Subject'] = SUBJECT 
        msg['From'] = SENDER 
        msg['To'] = ",".join(RECIPIENTS)
        textpart = MIMEText(BODY_TEXT)
        msg.attach(textpart)
        att = MIMEApplication(open(TMP_FILE_NAME, 'rb').read())
        att.add_header('Content-Disposition','attachment',filename="AmazonBedrock_Charges_last_24hr_each_Model_"+ str(getCurrentMilsec)+".csv")
        msg.attach(att)
        response = ses_client.send_raw_email(
            Source=SENDER,
            Destinations=RECIPIENTS,
            RawMessage={ 'Data':msg.as_string() }
        )

    except Exception as e:
        print("Something went wrong, please investigate")
        traceback.print_exc()
        return {
            'StatusCode': 400,
            'Message': 'Something went wrong, Please Investigate. Error --> '+ str(e)
        }