ActionController::Routing::Routes.draw do |map|

  map.resources :extensions, :profiles

  map.connect 'api/v1/:action/:id', :controller => 'api'
  map.connect 'api/v1/:action/:id.:format', :controller => 'api'
end
