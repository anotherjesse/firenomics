ActionController::Routing::Routes.draw do |map|

  map.resources :extensions, :profiles

  map.root :controller => 'site', :action => 'show'

  map.connect 'api/v1/:action/:id', :controller => 'api'
  map.connect 'api/v1/:action/:id.:format', :controller => 'api'
end
