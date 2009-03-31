class ExtensionsController < ApplicationController
  def index
    @extensions = Extension.all :order => 'name asc'
  end

  def show
    @extension = Extension.find(params[:id])
  end
end
