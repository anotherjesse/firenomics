class ExtensionsController < ApplicationController
  def index
    @extensions = Extension.all :order => 'name asc'
  end
end
