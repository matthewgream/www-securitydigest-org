#!/usr/bin/perl

#############################################################################################

package IO::String;

require 5.005_03;
use strict;
use vars qw($VERSION $DEBUG $IO_CONSTANTS);
$VERSION = "1.03";  # $Date: 2003/10/06 15:06:11 $

use Symbol ();

sub new
{
    my $class = shift;
    my $self = bless Symbol::gensym(), ref($class) || $class;
    tie *$self, $self;
    $self->open(@_);
    $self;
}

sub open
{
    my $self = shift;
    return $self->new(@_) unless ref($self);

    if (@_) {
	my $bufref = ref($_[0]) ? $_[0] : \$_[0];
	$$bufref = "" unless defined $$bufref;
	*$self->{buf} = $bufref;
    } else {
	my $buf = "";
	*$self->{buf} = \$buf;
    }
    *$self->{pos} = 0;
    *$self->{lno} = 0;
    $self;
}

sub pad
{
    my $self = shift;
    my $old = *$self->{pad};
    *$self->{pad} = substr($_[0], 0, 1) if @_;
    return "\0" unless defined($old) && length($old);
    $old;
}

sub dump
{
    require Data::Dumper;
    my $self = shift;
    print Data::Dumper->Dump([$self], ['*self']);
    print Data::Dumper->Dump([*$self{HASH}], ['$self{HASH}']);
}

sub TIEHANDLE
{
    print "TIEHANDLE @_\n" if $DEBUG;
    return $_[0] if ref($_[0]);
    my $class = shift;
    my $self = bless Symbol::gensym(), $class;
    $self->open(@_);
    $self;
}

sub DESTROY
{
    print "DESTROY @_\n" if $DEBUG;
}

sub close
{
    my $self = shift;
    delete *$self->{buf};
    delete *$self->{pos};
    delete *$self->{lno};
    if ($] >= 5.006 && $[ < 5.007) {
	# perl-5.6.x segfaults on untie, so avoid it
    }
    else {
	untie *$self;
	undef *$self;
    }
    $self;
}

sub opened
{
    my $self = shift;
    defined *$self->{buf};
}

sub getc
{
    my $self = shift;
    my $buf;
    return $buf if $self->read($buf, 1);
    return undef;
}

sub ungetc
{
    my $self = shift;
    $self->setpos($self->getpos() - 1)
}

sub eof
{
    my $self = shift;
    length(${*$self->{buf}}) <= *$self->{pos};
}

sub print
{
    my $self = shift;
    if (defined $\) {
	if (defined $,) {
	    $self->write(join($,, @_).$\);
	} else {
	    $self->write(join("",@_).$\);
	}
    } else {
	if (defined $,) {
	    $self->write(join($,, @_));
	} else {
	    $self->write(join("",@_));
	}
    }
}
*printflush = \*print;

sub printf
{
    my $self = shift;
    print "PRINTF(@_)\n" if $DEBUG;
    my $fmt = shift;
    $self->write(sprintf($fmt, @_));
}


my($SEEK_SET, $SEEK_CUR, $SEEK_END);

sub _init_seek_constants
{
    if ($IO_CONSTANTS) {
	require IO::Handle;
	$SEEK_SET = &IO::Handle::SEEK_SET;
	$SEEK_CUR = &IO::Handle::SEEK_CUR;
	$SEEK_END = &IO::Handle::SEEK_END;
    } else {
	$SEEK_SET = 0;
	$SEEK_CUR = 1;
	$SEEK_END = 2;
    }
}


sub seek
{
    my($self,$off,$whence) = @_;
    my $buf = *$self->{buf} || return;
    my $len = length($$buf);
    my $pos = *$self->{pos};

    _init_seek_constants() unless defined $SEEK_SET;

    if    ($whence == $SEEK_SET) { $pos = $off }
    elsif ($whence == $SEEK_CUR) { $pos += $off }
    elsif ($whence == $SEEK_END) { $pos = $len + $off }
    else { die "Bad whence ($whence)" }
    print "SEEK(POS=$pos,OFF=$off,LEN=$len)\n" if $DEBUG;

    $pos = 0 if $pos < 0;
    $self->truncate($pos) if $pos > $len;  # extend file
    *$self->{pos} = $pos;
}

sub pos
{
    my $self = shift;
    my $old = *$self->{pos};
    if (@_) {
	my $pos = shift || 0;
	my $buf = *$self->{buf};
	my $len = $buf ? length($$buf) : 0;
	$pos = $len if $pos > $len;
	*$self->{pos} = $pos;
    }
    $old;
}

sub getpos { shift->pos; }

*sysseek = \&seek;
*setpos  = \&pos;
*tell    = \&getpos;



sub getline
{
    my $self = shift;
    my $buf  = *$self->{buf} || return;
    my $len  = length($$buf);
    my $pos  = *$self->{pos};
    return if $pos >= $len;

    unless (defined $/) {  # slurp
	*$self->{pos} = $len;
	return substr($$buf, $pos);
    }

    unless (length $/) {  # paragraph mode
	# XXX slow&lazy implementation using getc()
	my $para = "";
	my $eol = 0;
	my $c;
	while (defined($c = $self->getc)) {
	    if ($c eq "\n") {
		$eol++;
	    } elsif ($eol > 1) {
		$self->ungetc($c);
		last;
	    }
	    $para .= $c;
	}
	return $para;   # XXX wantarray
    }

    my $idx = index($$buf,$/,$pos);
    if ($idx < 0) {
	# return rest of it
	*$self->{pos} = $len;
	$. = ++ *$self->{lno};
	return substr($$buf, $pos);
    }
    $len = $idx - $pos + length($/);
    *$self->{pos} += $len;
    $. = ++ *$self->{lno};
    return substr($$buf, $pos, $len);
}

sub getlines
{
    die "getlines() called in scalar context\n" unless wantarray;
    my $self = shift;
    my($line, @lines);
    push(@lines, $line) while defined($line = $self->getline);
    return @lines;
}

sub READLINE
{
    goto &getlines if wantarray;
    goto &getline;
}

sub input_line_number
{
    my $self = shift;
    my $old = *$self->{lno};
    *$self->{lno} = shift if @_;
    $old;
}

sub truncate
{
    my $self = shift;
    my $len = shift || 0;
    my $buf = *$self->{buf};
    if (length($$buf) >= $len) {
	substr($$buf, $len) = '';
	*$self->{pos} = $len if $len < *$self->{pos};
    } else {
	$$buf .= ($self->pad x ($len - length($$buf)));
    }
    $self;
}

sub read
{
    my $self = shift;
    my $buf = *$self->{buf};
    return unless $buf;

    my $pos = *$self->{pos};
    my $rem = length($$buf) - $pos;
    my $len = $_[1];
    $len = $rem if $len > $rem;
    if (@_ > 2) { # read offset
	substr($_[0],$_[2]) = substr($$buf, $pos, $len);
    } else {
	$_[0] = substr($$buf, $pos, $len);
    }
    *$self->{pos} += $len;
    return $len;
}

sub write
{
    my $self = shift;
    my $buf = *$self->{buf};
    return unless $buf;

    my $pos = *$self->{pos};
    my $slen = length($_[0]);
    my $len = $slen;
    my $off = 0;
    if (@_ > 1) {
	$len = $_[1] if $_[1] < $len;
	if (@_ > 2) {
	    $off = $_[2] || 0;
	    die "Offset outside string" if $off > $slen;
	    if ($off < 0) {
		$off += $slen;
		die "Offset outside string" if $off < 0;
	    }
	    my $rem = $slen - $off;
	    $len = $rem if $rem < $len;
	}
    }
    substr($$buf, $pos, $len) = substr($_[0], $off, $len);
    *$self->{pos} += $len;
    $len;
}

*sysread = \&read;
*syswrite = \&write;

sub stat
{
    my $self = shift;
    return unless $self->opened;
    return 1 unless wantarray;
    my $len = length ${*$self->{buf}};

    return (
     undef, undef,  # dev, ino
     0666,          # filemode
     1,             # links
     $>,            # user id
     $),            # group id
     undef,         # device id
     $len,          # size
     undef,         # atime
     undef,         # mtime
     undef,         # ctime
     512,           # blksize
     int(($len+511)/512)  # blocks
    );
}

sub FILENO {
    return undef;   # XXX perlfunc says this means the file is closed
}

sub blocking {
    my $self = shift;
    my $old = *$self->{blocking} || 0;
    *$self->{blocking} = shift if @_;
    $old;
}

my $notmuch = sub { return };

*fileno    = $notmuch;
*error     = $notmuch;
*clearerr  = $notmuch; 
*sync      = $notmuch;
*flush     = $notmuch;
*setbuf    = $notmuch;
*setvbuf   = $notmuch;

*untaint   = $notmuch;
*autoflush = $notmuch;
*fcntl     = $notmuch;
*ioctl     = $notmuch;

*GETC   = \&getc;
*PRINT  = \&print;
*PRINTF = \&printf;
*READ   = \&read;
*WRITE  = \&write;
*SEEK   = \&seek;
*TELL   = \&getpos;
*EOF    = \&eof;
*CLOSE  = \&close;

*BINMODE = $notmuch;


sub string_ref
{
    my $self = shift;
    *$self->{buf};
}
*sref = \&string_ref;

#############################################################################################

package cgi_buffer;
use strict;
use Digest::MD5;
use Compress::Zlib;
require 5.004;

$cgi_buffer::generate_etag = 1;
$cgi_buffer::compress_content = 1;


BEGIN {
	use Exporter();
	use vars qw($VERSION $buf $pos $headers $header $header_name $encoding
				$header_value $body @content_type $etag $send_body @o
				$i);
	$VERSION = 0.3;
	
	$cgi_buffer::buf = IO::String->new;
	$cgi_buffer::old_buf = select($cgi_buffer::buf);
}


END {	

	select($cgi_buffer::old_buf);
	$pos = $cgi_buffer::buf->getpos;
	$cgi_buffer::buf->setpos(0);
	read($cgi_buffer::buf, $buf, $pos);
	$buf = "" if (!$buf);
	($headers, $body) = split /\r?\n\r?\n/, $buf, 2;
	$headers = "" if (!$headers); $body = "" if (!$body);
	$send_body = 1;

	foreach $header (split(/\r?\n/, $headers)) {
		($header_name, $header_value) = split /\:\s*/, $header, 2;
		if (lc($header_name) eq 'content-type') {
			@content_type = split /\//, $header_value, 2;
		}
	}

	if ($cgi_buffer::compress_content) {
		foreach $encoding ('x-gzip', 'gzip') {
			$_ = lc($ENV{'HTTP_ACCEPT_ENCODING'});
			if ( m/$encoding/i && lc($content_type[0]) eq 'text') {
				$body = Compress::Zlib::memGzip($body);
				push @o, "Content-Encoding: $encoding";
				push @o, "Vary: Accept-Encoding";
				last;
			}
		}
	}

	if ($cgi_buffer::generate_etag) {
		$etag = '"' . Digest::MD5::md5_hex($body) . '"';
		push @o, "ETag: $etag";
		if ($ENV{'HTTP_IF_NONE_MATCH'}) {
			if ($etag =~ m/$ENV{'HTTP_IF_NONE_MATCH'}/) {
				push @o, "Status: 304 Not Modified";
				push @o, "";
				$send_body = 0;
			}
		}	
	}

	if ($send_body) {
		push @o, "Content-Length: " . length($body);
		push @o, $headers;
		push @o, "";
		push @o, $body;
	} 

	print join("\r\n", @o);
}


1;
