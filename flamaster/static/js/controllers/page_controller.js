// Generated by CoffeeScript 1.3.1
var __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; };

define(['chaplin/mediator', 'chaplin/controller', 'models/user', 'views/index_view', 'views/signup_view', 'views/dashboard_view'], function(mediator, Controller, User, IndexView, SignUpView, DashboardView) {
  'use strict';

  var PageController;
  return PageController = (function(_super) {

    __extends(PageController, _super);

    PageController.name = 'PageController';

    function PageController() {
      return PageController.__super__.constructor.apply(this, arguments);
    }

    PageController.prototype.historyURL = function(options) {
      console.log("PageController#historyURL", options);
      return options.path || '';
    };

    PageController.prototype.index = function() {
      return this.view = new DashboardView;
    };

    PageController.prototype.signup = function() {
      var nUser;
      nUser = User.extend({
        urlRoot: '/account/sessions/'
      });
      return this.view = new SignUpView({
        model: new nUser
      });
    };

    PageController.prototype.dashboard = function() {
      return this.view = new DashboardView;
    };

    return PageController;

  })(Controller);
});
