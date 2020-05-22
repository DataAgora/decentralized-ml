import React from 'react';
import Reflux from 'reflux';

import CoordinatorStore from '../../stores/CoordinatorStore';
import CoordinatorActions from '../../actions/CoordinatorActions';
import RepoDataActions from '../../actions/RepoDataActions';

class LaunchStep extends Reflux.Component {

    constructor(props) {
        super(props);
        this.store = CoordinatorStore;

        this.repoId = this.props.repoId
        this.apiKey = this.props.apiKey
        this.isDemo = this.props.isDemo;
        this.launchAuth = this.launchAuth.bind(this);
        this.launchExplora = this.launchExplora.bind(this);
        this.launchExploraImage = this.launchExploraImage.bind(this);
        this.launchExploraText = this.launchExploraText.bind(this);
        this.exploraAuthUrl = "http://" + this.props.ExploraUrl
        this.exploraURL = "http://" + this.repoId + ".explora.discreetai.com/notebooks/"
        this.copyApiKeyToClipboard = this.copyApiKeyToClipboard.bind(this);

        let authClicked = localStorage.getItem("authClicked" + this.repoId);
        if (!authClicked) {
            this.authClicked = false;
        } else {
            this.authClicked = true;
        }
    }

    componentDidMount() {
        CoordinatorActions.fetchCoordinatorStatus(this.props.repoId);
    }

    copyApiKeyToClipboard() {
        // const { match: { params } } = this.props;
        // const repoId = params.repoId;
        var dummy = document.createElement("textarea");
        document.body.appendChild(dummy);
        dummy.value = this.apiKey;
        dummy.select();
        document.execCommand("copy");
        document.body.removeChild(dummy);
      }

    launchAuth() {
        var close = function closeWindow(auth) {
            auth.close()
            localStorage.setItem("authClicked-" + this.repoId, true)
        }
        var auth = window.open(this.exploraAuthUrl, "_blank");
        this.authClicked = true;
        setTimeout(close, 300, auth)
    }

    launchExplora() {
        let url = this.exploraURL + "Explora.ipynb"
        var notebook = window.open(url, '_blank')
    }

    launchExploraImage() {
        let url = this.exploraURL + "ExploraMobileImage.ipynb"
        var notebook = window.open(url, '_blank')
    }

    launchExploraText() {
        let url = this.exploraURL + "ExploraMobileText.ipynb"
        var notebook = window.open(url, '_blank')
    }

    render() {
        const status = this.state.coordinatorStatuses[this.props.repoId];

        if (this.isDemo) {
            var authButton = (<button id="auth" onClick={this.launchAuth} className="btn btn-dark ml-2 explora"><b>Authenticate</b></button>)
            var launchButton = "";
            if (["ACTIVE", "AVAILABLE"].includes(status) && this.authClicked) {
                launchButton = <button id="image" onClick={this.launchExploraImage} className="btn btn-primary ml-2 explora"><b>Launch Explora</b></button>;
            } else {
                launchButton = <button id="image" disabled onClick={this.launchExploraImage} className="btn btn-primary ml-2 explora"><b>Launch Explora</b></button>;
            }
            return <li> {authButton}, then start your session by clicking on the following button: {launchButton}</li>
        } else {
            var authButton = (<button id="auth" onClick={this.launchAuth} className="btn btn-dark ml-2 explora"><b>Authenticate</b></button>)

            var exploraButton = "";
            var exploraImageButton = "";
            var exploraTextButton = "";

            if (["ACTIVE", "AVAILABLE"].includes(status) && this.authClicked) {
                exploraButton = <button id="reg" onClick={this.launchExplora} className="btn btn-xs explora btn-primary ml-2"><b>Explora.ipynb</b></button>;
                exploraImageButton = <button id="image" onClick={this.launchExploraImage} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileImage.ipynb</b></button>;
                exploraTextButton = <button id="text" onClick={this.launchExploraText} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileText.ipynb</b></button>;
            } else {
                exploraButton = <button id="reg" disabled onClick={this.launchExplora} className="btn btn-xs explora btn-primary ml-2"><b>Explora.ipynb</b></button>;
                exploraImageButton = <button id="image" disabled onClick={this.launchExploraImage} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileImage.ipynb</b></button>;
                exploraTextButton = <button id="text" disabled onClick={this.launchExploraText} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileText.ipynb</b></button>;
            }

            return <li>{authButton}, then choose one of the following notebooks, based on what type of session you want to run.
                <ul>
                    <br></br>
                    <li>{exploraButton} (Javascript/Python sessions)</li>
                    <br></br>
                    <li>{exploraImageButton} (iOS sessions with image models)</li>
                    <br></br>
                    <li>{exploraTextButton} (iOS sessions with text models)</li>
                </ul> 
            </li>
        }
        
    }
}

export default LaunchStep;
