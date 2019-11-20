# Dashboard API

The Dashboard API is a RESTful and serverless service used to create and manage DataAgora Repos.

## Set up

Before anything you need to install the [serverless](https://github.com/serverless/serverless) package by running:

```
npm install -g serverless
```

## Running locally

To run a server locally, you first need to install your Python dependencies:

```
pip install -r requirements.txt
```

Then, you can just run the following command to get the server running:

```
sls wsgi serve
```

## Deploying

To deploy, just run the following command:

```
sls deploy
```

Note that you need AWS properly configured in your machine for this to work.


## Tests

There aren't any tests available for this repo yet. Please help us write them!
