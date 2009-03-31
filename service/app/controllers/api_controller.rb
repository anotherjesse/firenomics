# import simplejson, uuid, md5, re
class ApiController < ApplicationController

  def update
    json = JSON.parse(params[:data])


    unless params[:id].blank?
      @profile = Profile.find_by_id(params[:id])

      if @profile
        if params[:sig] != @profile.sign(request.raw_post)
          render :status => 401, :text => '401 Unauthorized'
          return
        end
      end
    end

    unless @profile
      @send_welcome = @profile = Profile.new
    end

    @profile.update_attributes(:version => json['system']['version'],
                               :OS => json['system']['OS'],
                               :platform => json['system']['name'])

    # Build a dictionary of the current extensions
    existing = Hash.new
    @profile.profile_extensions.each do |pe|
      existing[pe.extension.mid] = pe
    end

    json['extensions'].each do |mid, ext_data|
      extension = Extension.find_by_mid(mid)

      unless extension
        attributes = ext_data.slice('name', 'updateRDF', 'description', 'creator',
                                    'homepageURL', 'developers', 'contributors',
                                    'translators')
        attributes[:mid] = mid
        extension = Extension.create attributes
      end

      if existing.has_key?(mid)
        existing[mid].update_attribute :version, ext_data['version']
        existing.delete(mid)
      else
        @profile.profile_extensions.create(:extension => extension,
                                           :version => ext_data['version'])
      end
    end

    # Delete any profile extensions that weren't in the update (uninstalled)
    existing.values.each &:destroy

    if @send_welcome
      render :status => (params[:id].blank? ? 200 : 410),
             :text => {'profile' => @profile.id, 'secret' => @profile.secret}.to_json
    else
      render :text => 'KTHXBAI'
    end
  end
end
