# Dashboard UI

UI for creating and managing DataAgora repos.

## Dependencies

Before anything, install the npm dependencies:

```
npm install
```

## Running locally

To run locally, just run

```
npm run build
```

then

```
npm run start
```

## Deploying

First do 

```
pip install s3cmd
``` 

and make sure AWS is set up on your local machine.

Then run

```
npm run build-and-deploy
```

Read `package.json` for available commands.
