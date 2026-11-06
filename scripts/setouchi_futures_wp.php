/* This file is passed as code to `wp eval`; it intentionally has no PHP opening tag. */
$request = json_decode(stream_get_contents(STDIN), true);
if (!is_array($request)) { echo json_encode(array('error' => 'Invalid request')); return; }
function setouchi_page($id) {
    $p = get_post($id);
    if (!$p || $p->post_type !== 'page') { throw new Exception('Page not found'); }
    return array('id' => (int)$p->ID, 'link' => get_permalink($id), 'status' => $p->post_status,
        'slug' => $p->post_name, 'parent' => (int)$p->post_parent,
        'template' => (get_page_template_slug($id) ?: ''), 'modified_gmt' => $p->post_modified_gmt,
        'title' => array('raw' => $p->post_title),
        'content' => array('raw' => $p->post_content));
}
function setouchi_media($id) {
    return array('id' => (int)$id, 'slug' => get_post_field('post_name', $id),
        'source_url' => wp_get_attachment_url($id));
}
try {
    $id = (int)$request['page_id'];
    switch ($request['op']) {
        case 'get_page': $result = setouchi_page($id); break;
        case 'find_media':
            $items = get_posts(array('post_type' => 'attachment', 'post_status' => 'inherit',
                'name' => $request['slug'], 'numberposts' => 2));
            if (count($items) > 1) { throw new Exception('Duplicate media slug'); }
            $result = $items ? setouchi_media($items[0]->ID) : null;
            break;
        case 'upload':
            require_once ABSPATH . 'wp-admin/includes/file.php';
            require_once ABSPATH . 'wp-admin/includes/image.php';
            $bytes = base64_decode($request['data'], true);
            if ($bytes === false) { throw new Exception('Invalid media data'); }
            $upload = wp_upload_bits(sanitize_file_name($request['filename']), null, $bytes);
            if ($upload['error']) { throw new Exception('Media write failed'); }
            $type = wp_check_filetype($upload['file']);
            $media_id = wp_insert_attachment(wp_slash(array('post_title' => $request['title'],
                'post_excerpt' => $request['caption'], 'post_name' => $request['slug'],
                'post_mime_type' => $type['type'], 'post_status' => 'inherit', 'post_parent' => $id)), $upload['file'], $id, true);
            if (is_wp_error($media_id)) { throw new Exception('Media registration failed'); }
            update_post_meta($media_id, '_wp_attachment_image_alt', wp_slash($request['alt']));
            wp_update_attachment_metadata($media_id, wp_generate_attachment_metadata($media_id, $upload['file']));
            $result = setouchi_media($media_id);
            break;
        case 'update':
            $before = setouchi_page($id);
            if (hash('sha256', $before['content']['raw']) !== $request['expected_hash']) {
                throw new Exception('Page changed immediately before update; re-plan');
            }
            /* Recheck is not a database-level CAS; external editors do not share a lock. */
            $saved = wp_update_post(wp_slash(array('ID' => $id, 'post_content' => $request['content'])), true);
            if (is_wp_error($saved)) { throw new Exception('Page update failed'); }
            $result = setouchi_page($id);
            break;
        default: throw new Exception('Unknown operation');
    }
    echo wp_json_encode($result);
} catch (Exception $error) {
    echo wp_json_encode(array('error' => $error->getMessage()));
}
