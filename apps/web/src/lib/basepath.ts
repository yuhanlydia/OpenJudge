export function sitePath(path:string,base='/'){const prefix=base.replace(/^\/+|\/+$/g,'');return '/'+(prefix?prefix+'/':'')+path.replace(/^\/+/,'');}
export function safeSource(source:unknown):string|null{try{const u=new URL(String(source));return u.protocol==='https:'&&['openreview.net','api2.openreview.net','blog.iclr.cc','iclr.cc'].includes(u.hostname)?u.href:null;}catch{return null;}}
