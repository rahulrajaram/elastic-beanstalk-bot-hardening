## 1. Hardening AWS EB (Elastic Beanstalk) app against bots

This repository contains a Python application meant to be launched as an Elastic Beanstalk web application on AWS cloud and serves as an example of how to protect your EB applications again bots on the Internet without using [AWS WAF](https://docs.aws.amazon.com/waf/latest/developerguide/waf-bot-control.html) and just those tools that EB traditionally interacts with or provides.

## 2. Prerequisites
1. AWS account: ensure you have an AWS account that you can access and that you have IAM user credentials in `~/.aws/credentials`
2. Python: ensure Python's installed on your system. If not download and install [from here](https://www.python.org/downloads/).
3. pip: Installing Python should also installed `pip`. If you can't find `pip`, download the [get-pip.py](https://bootstrap.pypa.io/get-pip.py) file and run it with `python`
4. virtualenv:
    - Install `virtualenv`: `pip install virtualenv`
    - Create a virtual-env and activate it. [See](https://virtualenv.pypa.io/en/latest/user_guide.html).
5. curl: Download and install curl from [here](https://curl.se/download.html)

## 3. Launching the app
1. Run:
    ```
    git clone https://github.com/rahulrajaram/elastic-beanstalk-bot-hardening && cd elastic-beanstalk-bot-hardening
    ```
2. Run:
    ```
    pip install -r requirements.txt
    ```
3. Run:
    ```
    eb init -i
    ```
    and choose appropriate values for application and region. Additionally:
    - Select the latest Python and
    - Choose to associate a SSH key with your EC2 instances
4. Run:
    ```
    eb create bad-request-blocker
    ```
5. Run:
    ```
    eb status bad-request-blocker
    ```
6. Pick out the CNAME from the output of 5. and access it through your browser. This should succeed.
7. Append **'/yolo'** to your CNAME and visit it. This should redirect you to **'/'**

## 4. Reviewing .ebextensions
1. review the `.ebextensions/listenerrules.config` file. This file defines 2 resources:
    
    a. **`AWSEBV2LoadBalancerListenerBlock`**: a catch-all listener rule for any path-pattern anything *other than* **'/'**, such as **'/yolo'**. This is programmed to redirect to **'/'** with a HTTP 301.
    
    **'/?*'** in particular reads: "**'/'** followed by a single character and then how many ever after that.'. This rule is associated with **AWSEBV2LoadBalancerListener**, which is an ELBv2 listener defined by EB on the application's ALB. EB will combine this template with the one that it generates in the backend and reconcile connections like this one.
    
    b. **`AWSEBV2LoadBalancerListenerMain`**: a listener rule for the **'/'** path-pattern and all extensions of it involving only query-params in addition. This is programmed to take you to the index page of the app. It merely redirects traffic to the target-group of the application. This rule too is associated with **`AWSEBV2LoadBalancerListener`**. The **`ForwardAaction`** specifies that all traffic received at this listener must be forwarded to the target-group created by EB for the environment (and as an extension to the EC2 instances)

(Note: since these resources have been injected into the Cloud Formation template, they have bypassed EB option-settings that we could have used to do something similar. The reason we didn't use option-settings was the lack of support for any action type other than "forward". Specifically, there is no support for redirects through EB without the use of .ebextensions.)

## 5. Sending traffic to your application
1. From one terminal run:

    ```
    while true ; do ; curl --silent -i <insert CNAME here> >/dev/null;  done
    ```
    This will invoke youyr webapp successfully indefinitely.
2. From another terminal run and *keep this open*:

    ```
    while true ; do ; curl --silent -i <insert CNAME here>/yolo >/dev/null;  done
    ```
    This will cause your app to return 400s indefinitely.
3. From your application workspace, run:
    ```
    eb health --refresh
    ```
    This will show the realtime health of your application.
    
    Within 30s of executing 1. and 2., you should be able to observe that your environment is healthy because all traffic arriving at it is at **'/'** by virtue of the redirect at the Load Balancer.
    
    You can verify through `curl -i <insert CNAME here>/yolo` that the LB is indeed redirecting.
    
    You could additionally also set up access logging for your ALB.

## 6. Hardening Nginx
1. While at this your application is protected at the ALB level, it is good practice to also ensure your application's Nginx is configured similarly. Examine the `.platform/nginx/nginx.conf` file. This file is almost identical to the one EB would define for you, but for the following override which is identical semantically to the above ELBv2 listener rule redirect. A notable addition beyond the redirect is a reinstatement of the `'/health'` path, which must continue existing and pointing to the `'/health'` endpoint in the Flask app so that the ELB is able to verify that the instances are alive.

    ```
    # Redirect /?* to /
    location ~ ^/.+ {
        return 301 /;
    }


    # Ensure /health is served normally
    location = /health {
        proxy_pass http://localhost:8000/health;
    }
    ```
