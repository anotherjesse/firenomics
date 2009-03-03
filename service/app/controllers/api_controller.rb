# import simplejson, uuid, md5, re
class ApiController < ApplicationController

  def update
    key = params[:key]
    send_welcome = false
    json = simplejson.loads(params[:data])

    if !key.blank?
      profile = Profile.find_by_id(key)

      if profile
        sig = web.input().sig
        data = web.data()
        expected = md5.new(data + profile.secret).hexdigest()
        if sig != expected
          web.ctx.status = "401 Unauthorized"
          return "Invalid Signature"
        else
          send_welcome = 410
        end
      else
        send_welcome = 200
      end
    end

    if send_welcome
      profile = Profile.new
    end

    profile.version = json['system']['version']
    profile.os = json['system']['OS']
    profile.platform = json['system']['name']
    profile.save

    # Build a dictionary of the current extensions
    profile_extensions = profile.profile_extensions

    px_dict = Hash.new
    profile_extensions.each { |pe| px_dict[pe.extension.mid] = pe }


    local_extensions = json['extensions']
    local_extensions.each do |local_extension|
      mid = local_extension['mid']
      extension = Extension.find_by_mid(mid)
      if extension.nil?
        puts "new extension: " + mid
        extension = Extension.new
        extension.mid = mid
        extension.name = local_extension['name']
        extension.updateRDF = local_extension['updateRDF']
        extension.description = local_extension['description']
        extension.creator = local_extension['creator']
        extension.homepageURL = local_extension['homepageURL']
        extension.developers = local_extension['developers']
        extension.translators = local_extension['translators']
        extension.contributors = local_extension['contributors']
        extension.save
      end

      if px_dict.has_key(mid)
        px_dict[mid].update_attribute :version, local_extension['version']
        del px_dict[mid]
      else
        px = ProfileExtension.new
        px.extension = extension
        px.version = local_extension['version']
        px.profile = profile
        px.save
      end
    end

    # Delete any user extensions from the database that weren't in the update
    for px in px_dict
      puts "user no longer has extension " + px
      px_dict[px].destroy
    end

    if send_welcome
#      web.ctx.status = "%s New Profile" % send_welcome
      #      web.header('Content-Type', 'text/x-json')

      render :text => 'hi'
#      return simplejson.dumps({'profile': str(profile.key()), 'secret': profile.secret})
    else
      render :text => 'KTHXBAI'
    end
  end
end
