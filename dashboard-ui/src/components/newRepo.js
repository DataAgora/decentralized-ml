import React from 'react';
import Reflux from 'reflux';
import ReactDOM from 'react-dom';
import { Link } from 'react-router-dom';

import RepoDataStore from './../stores/RepoDataStore';
import RepoDataActions from './../actions/RepoDataActions';

import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';


class NewRepo extends Reflux.Component {

  constructor(props) {
    super(props);
    this.store = RepoDataStore;
  }

  componentDidMount() {
    RepoDataActions.fetchReposRemaining();
  }

  _handleSubmit(event) {
    event.preventDefault();

    let form = document.getElementById('newRepoForm');

    if (form.reportValidity()) {
      let repoName = ReactDOM.findDOMNode(this.refs.repoName).value.replace(/[^a-zA-Z0-9-]/g,'-');
      document.getElementById("wait").hidden = false;
      RepoDataActions.createNewRepo(
        repoName,
        ReactDOM.findDOMNode(this.refs.repoDescription).value
      );
    }
  }

  _handleContinue(event) {
    event.preventDefault();
    RepoDataActions.resetState();
    this.props.history.push("/repo/" + this.state.creationState.repoId);
  }

  render() {
    // Get number of repos left.
    if (this.state.creationState.loading === true) {
      return (
        <div className="text-center text-secondary">
          <FontAwesomeIcon icon="sync" size="lg" spin />
        </div>
      );
    }

    if (this.state.creationState.created) {
      return (
        <div>
          <div className="row text-center">
            <div className="col-2"></div>
            <div className="col-8">
              <h3>Important!</h3>
              <h5 className="mt-4">The new repo was created and your <b>API Key</b> is shown below.</h5>
              <h5>Please save it!</h5>
              <h5>You won't be able to access it again and you will need it to hook up clients to this repo.</h5>
              <br /><br />
              <h6 className="text-success">{this.state.creationState.apiKey}</h6>
              <br /><br />
              <div>
                <button type="submit" className="btn btn-lg btn-info" onClick={this._handleContinue.bind(this)}>Continue (I have saved the key)</button>
              </div>
            </div>
          </div>

        </div>
      )
    }

    let reposLeft = this.state.creationState.reposRemaining;
    if (!reposLeft) {
      return (
        <div className="text-center">
          <h3>Sorry, but you have no more repos left.</h3>
          <p className="mt-4">If you want to upgrade your account to support more repos, <a href="mailto:neelesh.dodda@discreetai.com?subject=Upgrade Account&body=I would like to upgrade my account!">please email us</a>.</p>
          <p className="mt-3"><Link to="/">Back to dashboard</Link></p>
        </div>
      );
    } else {
      return (
        <div className="row">
          <div className="col-4"></div>
          <div className="col-4">
            <h3>Create a new repo</h3>
            <p className="mt-3">A <b>repo</b> is a link to a network of devices, history of training, and resulting models.</p>
            <p className="mt-3">Create a new repository to start doing private federated learning. Repos are private by default.</p>
            <form id="newRepoForm" className="mt-4">
              <div className="form-group">
               <label htmlFor="repoNameInput">Repo name</label>
               <input type="text" className="form-control" id="repoNameInput" ref="repoName" aria-describedby="repoName" placeholder="awesome-dml-experiment" required/>
               <small id="repoNameHelp" className="form-text text-muted">Use a repo name you haven't used yet. Make it catchy.</small>
              </div>
              <div className="form-group">
               <label htmlFor="repoDescriptionInput">Brief description</label>
               <input type="text" className="form-control" id="repoDescriptionInput" ref="repoDescription" placeholder="To do magic on users' data without even seeing it." maxLength="80" required/>
               <small id="repoDescriptionHelp" className="form-text text-muted">Anything will do. Use this to remember what a repo is about.</small>
              </div>
              <div className="text-center mt-5">
                <button type="submit" className={"btn btn-lg btn-primary " + (this.state.creationState.creating ? "disabled" : "")} onClick={this._handleSubmit.bind(this)}>Create Repo</button>
              </div>
              <p id="wait" hidden="true" className="mt-3">Please wait...</p>
            </form>
          </div>
        </div>
      );
    }
  }
}

export default NewRepo;
