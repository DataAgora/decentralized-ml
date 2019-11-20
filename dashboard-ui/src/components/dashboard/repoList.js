import React from 'react';
import Reflux from 'reflux';
import { Link, withRouter } from "react-router-dom";

import RepoStatus from './../repo/repoStatus';

import DashboardStore from './../../stores/DashboardStore';
import DashboardActions from './../../actions/DashboardActions';

import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';

var username = null;
var repo_id = null;

class RepoList extends Reflux.Component {

  constructor(props) {
    super(props);
    this.store = DashboardStore;
  }

  componentDidMount() {
    DashboardActions.fetchAllRepos();
  }

  render() {
    if (this.state.error !== false) {
      return <div className="text-center"><p>Error: {this.state.error}</p></div>
    }

    if (this.state.loading === true) {
      return (
        <div className="text-center text-secondary">
          <FontAwesomeIcon icon="sync" size="lg" spin />
        </div>
      );
    }

    if (this.state.repos.length === 0) {
      return (
        <div>
           <h3 className="text-center">You don't own any repos yet.</h3>
           <p className="lead text-center mt-4">
             Start by creating <Link to="new" className="lead">a new repo.</Link>
           </p>
        </div>
      )
    } else {
      var deleteRepo = this.deleteRepo
      return (
        <div class="row">
          <div class="col">
            {this.state.repos.map(function(repo, index) {
              let createdLessThan10MinutesAgo = Math.floor(Date.now()/1000) < (repo.CreatedAt + 60*10);
              repo_id = repo;
              return (
                <div className="jumbotron" key={index}>
                  <div className="row">
                    <div className="col">
                      <h4 className="d-inline mr-3"><Link to={"repo/" + repo.Id} className="display-5 text-black">{repo.Name}</Link></h4>
                      <RepoStatus repoId={repo.Id} isDeploying={createdLessThan10MinutesAgo} />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )
    }
  }
}

export default withRouter(RepoList);
