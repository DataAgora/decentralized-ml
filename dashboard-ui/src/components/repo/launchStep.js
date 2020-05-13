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
        this.isDemo = this.props.isDemo;
        this.launchExplora = this.launchExplora.bind(this);
        this.launchExploraImage = this.launchExploraImage.bind(this);
        this.launchExploraText = this.launchExploraText.bind(this);
        this.exploraURL = "http://" + this.repoId + ".explora.discreetai.com/notebooks/"
    }

    componentDidMount() {
        CoordinatorActions.fetchCoordinatorStatus(this.props.repoId);
    }

    launchExplora() {
        var win = window.open(this.exploraURL + "Explora.ipynb", '_blank');
        win.focus();
    }

    launchExploraImage() {
        var win = window.open(this.exploraURL + "ExploraMobileImage.ipynb", '_blank');
        win.focus();
    }

    launchExploraText() {
        var win = window.open(this.exploraURL + "ExploraMobileText.ipynb", '_blank');
        win.focus();
    }

    render() {
        const status = this.state.coordinatorStatuses[this.props.repoId];

        if (this.isDemo) {
            var button = "";
            if (["ACTIVE", "AVAILABLE"].includes(status)) {
                button = <button onClick={this.launchExploraImage} className="btn btn-primary ml-2"><b>Launch Explora</b></button>;
            } else {
                button = <button disabled onClick={this.launchExploraImage} className="btn btn-primary ml-2"><b>Launch Explora</b></button>;
            }
            return <li>Start your session by clicking the following button: {button}</li>
        } else {
            var exploraButton = "";
            var exploraImageButton = "";
            var exploraTextButton = "";

            if (["ACTIVE", "AVAILABLE"].includes(status)) {
                exploraButton = <button onClick={this.launchExplora} className="btn btn-xs explora btn-primary ml-2"><b>Explora.ipynb</b></button>;
                exploraImageButton = <button onClick={this.launchExploraImage} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileImage.ipynb</b></button>;
                exploraTextButton = <button onClick={this.launchExploraText} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileText.ipynb</b></button>;
            } else {
                exploraButton = <button disabled onClick={this.launchExplora} className="btn btn-xs explora btn-primary ml-2"><b>Explora.ipynb</b></button>;
                exploraImageButton = <button disabled onClick={this.launchExploraImage} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileImage.ipynb</b></button>;
                exploraTextButton = <button disabled onClick={this.launchExploraText} className="btn btn-xs explora btn-primary ml-2"><b>ExploraMobileText.ipynb</b></button>;
            }

            return <li>Open the notebook {exploraButton} for Javascript/Python sessions. Open the notebook {exploraImageButton} and {exploraTextButton} for iOS sessions with image and text models respectively.</li>
        }
        
    }
}

export default LaunchStep;
