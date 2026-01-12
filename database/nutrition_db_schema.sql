--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2026-01-12 22:12:57

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE "DATN";
--
-- TOC entry 5144 (class 1262 OID 17727)
-- Name: DATN; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE "DATN" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Vietnamese_Vietnam.1258';


ALTER DATABASE "DATN" OWNER TO postgres;

\connect "DATN"

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 17728)
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- TOC entry 5145 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- TOC entry 3 (class 3079 OID 17809)
-- Name: unaccent; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;


--
-- TOC entry 5146 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION unaccent; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 17816)
-- Name: account; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account (
    id integer NOT NULL,
    username character varying(255),
    password character varying(255),
    iscollectioninfo integer
);


ALTER TABLE public.account OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 17821)
-- Name: account_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.account_id_seq OWNER TO postgres;

--
-- TOC entry 5147 (class 0 OID 0)
-- Dependencies: 220
-- Name: account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.account_id_seq OWNED BY public.account.id;


--
-- TOC entry 221 (class 1259 OID 17822)
-- Name: activitylevel; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.activitylevel (
    id integer NOT NULL,
    title character varying(255),
    url character varying(255),
    value real,
    detail text
);


ALTER TABLE public.activitylevel OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 17827)
-- Name: activitylevel_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.activitylevel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.activitylevel_id_seq OWNER TO postgres;

--
-- TOC entry 5148 (class 0 OID 0)
-- Dependencies: 222
-- Name: activitylevel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.activitylevel_id_seq OWNED BY public.activitylevel.id;


--
-- TOC entry 223 (class 1259 OID 17828)
-- Name: diet; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.diet (
    id integer NOT NULL,
    title character varying(255),
    detail character varying(255)
);


ALTER TABLE public.diet OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 17833)
-- Name: diet_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.diet_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.diet_id_seq OWNER TO postgres;

--
-- TOC entry 5149 (class 0 OID 0)
-- Dependencies: 224
-- Name: diet_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.diet_id_seq OWNED BY public.diet.id;


--
-- TOC entry 225 (class 1259 OID 17834)
-- Name: dish; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dish (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    thumbnail character varying(255),
    isconfirm integer,
    description text,
    preparationsteps text,
    cookingsteps text
);


ALTER TABLE public.dish OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 17839)
-- Name: dish_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dish_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dish_id_seq OWNER TO postgres;

--
-- TOC entry 5150 (class 0 OID 0)
-- Dependencies: 226
-- Name: dish_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dish_id_seq OWNED BY public.dish.id;


--
-- TOC entry 227 (class 1259 OID 17840)
-- Name: drinkofuser; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.drinkofuser (
    id integer NOT NULL,
    "time" timestamp without time zone,
    amount real,
    unitdrinkid integer,
    userinfoid integer,
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.drinkofuser OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 17844)
-- Name: drinkofuser_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.drinkofuser_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.drinkofuser_id_seq OWNER TO postgres;

--
-- TOC entry 5151 (class 0 OID 0)
-- Dependencies: 228
-- Name: drinkofuser_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.drinkofuser_id_seq OWNED BY public.drinkofuser.id;


--
-- TOC entry 229 (class 1259 OID 17845)
-- Name: exercise; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exercise (
    id integer NOT NULL,
    nameexercise character varying(255) NOT NULL,
    detail text,
    thumbnail character varying(255)
);


ALTER TABLE public.exercise OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 17850)
-- Name: exercise_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.exercise_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exercise_id_seq OWNER TO postgres;

--
-- TOC entry 5152 (class 0 OID 0)
-- Dependencies: 230
-- Name: exercise_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.exercise_id_seq OWNED BY public.exercise.id;


--
-- TOC entry 231 (class 1259 OID 17851)
-- Name: exerciseofuser; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exerciseofuser (
    id integer NOT NULL,
    "time" timestamp without time zone NOT NULL,
    minute integer NOT NULL,
    levelexerciseid integer NOT NULL,
    userinfoid integer NOT NULL,
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.exerciseofuser OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 17855)
-- Name: exerciseofuser_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.exerciseofuser_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exerciseofuser_id_seq OWNER TO postgres;

--
-- TOC entry 5153 (class 0 OID 0)
-- Dependencies: 232
-- Name: exerciseofuser_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.exerciseofuser_id_seq OWNED BY public.exerciseofuser.id;


--
-- TOC entry 233 (class 1259 OID 17856)
-- Name: hashtag; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hashtag (
    id integer NOT NULL,
    title character varying(255)
);


ALTER TABLE public.hashtag OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 17859)
-- Name: hashtag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hashtag_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hashtag_id_seq OWNER TO postgres;

--
-- TOC entry 5154 (class 0 OID 0)
-- Dependencies: 234
-- Name: hashtag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hashtag_id_seq OWNED BY public.hashtag.id;


--
-- TOC entry 235 (class 1259 OID 17860)
-- Name: hashtagofdish; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hashtagofdish (
    id integer NOT NULL,
    hashtagid integer NOT NULL,
    dishid integer NOT NULL
);


ALTER TABLE public.hashtagofdish OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 17863)
-- Name: hashtagofdish_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hashtagofdish_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hashtagofdish_id_seq OWNER TO postgres;

--
-- TOC entry 5155 (class 0 OID 0)
-- Dependencies: 236
-- Name: hashtagofdish_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hashtagofdish_id_seq OWNED BY public.hashtagofdish.id;


--
-- TOC entry 237 (class 1259 OID 17864)
-- Name: healthstatus; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.healthstatus (
    id integer NOT NULL,
    title character varying(255)
);


ALTER TABLE public.healthstatus OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 17867)
-- Name: healthstatus_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.healthstatus_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.healthstatus_id_seq OWNER TO postgres;

--
-- TOC entry 5156 (class 0 OID 0)
-- Dependencies: 238
-- Name: healthstatus_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.healthstatus_id_seq OWNED BY public.healthstatus.id;


--
-- TOC entry 239 (class 1259 OID 17868)
-- Name: healthstatususer; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.healthstatususer (
    id integer NOT NULL,
    userinfoid integer,
    healthstatusid integer
);


ALTER TABLE public.healthstatususer OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 17871)
-- Name: healthstatususer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.healthstatususer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.healthstatususer_id_seq OWNER TO postgres;

--
-- TOC entry 5157 (class 0 OID 0)
-- Dependencies: 240
-- Name: healthstatususer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.healthstatususer_id_seq OWNED BY public.healthstatususer.id;


--
-- TOC entry 241 (class 1259 OID 17872)
-- Name: importanthashtag; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.importanthashtag (
    id integer NOT NULL,
    requiredindexid integer,
    hashtagid integer,
    typerequest character varying(255)
);


ALTER TABLE public.importanthashtag OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 17875)
-- Name: importanthashtag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.importanthashtag_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.importanthashtag_id_seq OWNER TO postgres;

--
-- TOC entry 5158 (class 0 OID 0)
-- Dependencies: 242
-- Name: importanthashtag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.importanthashtag_id_seq OWNED BY public.importanthashtag.id;


--
-- TOC entry 243 (class 1259 OID 17876)
-- Name: ingredient; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ingredient (
    id integer NOT NULL,
    name character varying(255),
    thumbnail character varying(255),
    baseunit character varying(255),
    gramperunit real,
    isconfirm integer,
    kcal integer,
    carbs real,
    sugar real,
    fiber real,
    protein real,
    saturatedfat real,
    monounsaturatedfat real,
    polyunsaturatedfat real,
    transfat real,
    cholesterol real,
    vitamina real,
    vitamind real,
    vitaminc real,
    vitaminb6 real,
    vitaminb12 real,
    vitamine real,
    vitamink real,
    choline real,
    canxi real,
    fe real,
    magie real,
    photpho real,
    kali real,
    natri real,
    zn real,
    water real,
    caffeine real,
    alcohol real
);


ALTER TABLE public.ingredient OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 17881)
-- Name: ingredient_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ingredient_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ingredient_id_seq OWNER TO postgres;

--
-- TOC entry 5159 (class 0 OID 0)
-- Dependencies: 244
-- Name: ingredient_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ingredient_id_seq OWNED BY public.ingredient.id;


--
-- TOC entry 245 (class 1259 OID 17882)
-- Name: ingredientindish; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ingredientindish (
    id integer NOT NULL,
    weight real NOT NULL,
    ingredientid integer NOT NULL,
    dishid integer NOT NULL
);


ALTER TABLE public.ingredientindish OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 17885)
-- Name: ingredientindish_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ingredientindish_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ingredientindish_id_seq OWNER TO postgres;

--
-- TOC entry 5160 (class 0 OID 0)
-- Dependencies: 246
-- Name: ingredientindish_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ingredientindish_id_seq OWNED BY public.ingredientindish.id;


--
-- TOC entry 247 (class 1259 OID 17886)
-- Name: levelexercise; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.levelexercise (
    id integer NOT NULL,
    level character varying(255) NOT NULL,
    kcalpermin integer,
    exerciseid integer NOT NULL
);


ALTER TABLE public.levelexercise OWNER TO postgres;

--
-- TOC entry 248 (class 1259 OID 17889)
-- Name: levelexercise_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.levelexercise_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.levelexercise_id_seq OWNER TO postgres;

--
-- TOC entry 5161 (class 0 OID 0)
-- Dependencies: 248
-- Name: levelexercise_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.levelexercise_id_seq OWNED BY public.levelexercise.id;


--
-- TOC entry 249 (class 1259 OID 17890)
-- Name: limitfood; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.limitfood (
    id integer NOT NULL,
    title character varying(255),
    detail character varying(255)
);


ALTER TABLE public.limitfood OWNER TO postgres;

--
-- TOC entry 250 (class 1259 OID 17895)
-- Name: limitfood_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.limitfood_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.limitfood_id_seq OWNER TO postgres;

--
-- TOC entry 5162 (class 0 OID 0)
-- Dependencies: 250
-- Name: limitfood_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.limitfood_id_seq OWNED BY public.limitfood.id;


--
-- TOC entry 251 (class 1259 OID 17896)
-- Name: limitfooduser; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.limitfooduser (
    id integer NOT NULL,
    userinfoid integer,
    limitfoodid integer
);


ALTER TABLE public.limitfooduser OWNER TO postgres;

--
-- TOC entry 252 (class 1259 OID 17899)
-- Name: limitfooduser_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.limitfooduser_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.limitfooduser_id_seq OWNER TO postgres;

--
-- TOC entry 5163 (class 0 OID 0)
-- Dependencies: 252
-- Name: limitfooduser_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.limitfooduser_id_seq OWNED BY public.limitfooduser.id;


--
-- TOC entry 253 (class 1259 OID 17900)
-- Name: mealofuser; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mealofuser (
    id integer NOT NULL,
    "time" timestamp without time zone,
    mealtype character varying(255),
    weight real,
    userinfoid integer,
    dishid integer,
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.mealofuser OWNER TO postgres;

--
-- TOC entry 254 (class 1259 OID 17904)
-- Name: mealofuser_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.mealofuser_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mealofuser_id_seq OWNER TO postgres;

--
-- TOC entry 5164 (class 0 OID 0)
-- Dependencies: 254
-- Name: mealofuser_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.mealofuser_id_seq OWNED BY public.mealofuser.id;


--
-- TOC entry 255 (class 1259 OID 17905)
-- Name: notification; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification (
    id integer NOT NULL,
    senderid integer NOT NULL,
    receiverid integer NOT NULL,
    type character varying(30) NOT NULL,
    content text NOT NULL,
    relatedid integer NOT NULL,
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) DEFAULT 'UNREAD'::character varying
);


ALTER TABLE public.notification OWNER TO postgres;

--
-- TOC entry 256 (class 1259 OID 17912)
-- Name: notification_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notification_id_seq OWNER TO postgres;

--
-- TOC entry 5165 (class 0 OID 0)
-- Dependencies: 256
-- Name: notification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notification_id_seq OWNED BY public.notification.id;


--
-- TOC entry 257 (class 1259 OID 17913)
-- Name: requiredindex; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.requiredindex (
    id integer NOT NULL,
    userinfoid integer,
    bmr real,
    tdee real,
    targetcalories real,
    water real,
    protein real,
    totalfat real,
    saturatedfat real,
    monounsaturatedfat real,
    polyunsaturatedfat real,
    transfat real,
    carbohydrate real,
    carbs real,
    sugar real,
    fiber real,
    cholesterol real,
    vitamina real,
    vitamind real,
    vitaminc real,
    vitaminb6 real,
    vitaminb12 real,
    vitamine real,
    vitamink real,
    choline real,
    canxi real,
    fe real,
    magie real,
    photpho real,
    kali real,
    natri real,
    zn real,
    caffeine real,
    alcohol real
);


ALTER TABLE public.requiredindex OWNER TO postgres;

--
-- TOC entry 258 (class 1259 OID 17916)
-- Name: requiredindex_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.requiredindex_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.requiredindex_id_seq OWNER TO postgres;

--
-- TOC entry 5166 (class 0 OID 0)
-- Dependencies: 258
-- Name: requiredindex_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.requiredindex_id_seq OWNED BY public.requiredindex.id;


--
-- TOC entry 259 (class 1259 OID 17917)
-- Name: unitdrink; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.unitdrink (
    id integer NOT NULL,
    baseunit character varying(255),
    mlperunit integer,
    thumbnail character varying(255)
);


ALTER TABLE public.unitdrink OWNER TO postgres;

--
-- TOC entry 260 (class 1259 OID 17922)
-- Name: unitdrink_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.unitdrink_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.unitdrink_id_seq OWNER TO postgres;

--
-- TOC entry 5167 (class 0 OID 0)
-- Dependencies: 260
-- Name: unitdrink_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.unitdrink_id_seq OWNED BY public.unitdrink.id;


--
-- TOC entry 261 (class 1259 OID 17923)
-- Name: userinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.userinfo (
    id integer NOT NULL,
    fullname character varying(255),
    gender character varying(255),
    age integer,
    height integer,
    weight integer,
    weighttarget integer,
    datetarget date,
    accountid integer,
    activitylevelid integer,
    dietid integer,
    token text
);


ALTER TABLE public.userinfo OWNER TO postgres;

--
-- TOC entry 262 (class 1259 OID 17928)
-- Name: userinfo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.userinfo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.userinfo_id_seq OWNER TO postgres;

--
-- TOC entry 5168 (class 0 OID 0)
-- Dependencies: 262
-- Name: userinfo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.userinfo_id_seq OWNED BY public.userinfo.id;


--
-- TOC entry 4902 (class 2604 OID 17929)
-- Name: account id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account ALTER COLUMN id SET DEFAULT nextval('public.account_id_seq'::regclass);


--
-- TOC entry 4903 (class 2604 OID 17930)
-- Name: activitylevel id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activitylevel ALTER COLUMN id SET DEFAULT nextval('public.activitylevel_id_seq'::regclass);


--
-- TOC entry 4904 (class 2604 OID 17931)
-- Name: diet id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diet ALTER COLUMN id SET DEFAULT nextval('public.diet_id_seq'::regclass);


--
-- TOC entry 4905 (class 2604 OID 17932)
-- Name: dish id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dish ALTER COLUMN id SET DEFAULT nextval('public.dish_id_seq'::regclass);


--
-- TOC entry 4906 (class 2604 OID 17933)
-- Name: drinkofuser id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drinkofuser ALTER COLUMN id SET DEFAULT nextval('public.drinkofuser_id_seq'::regclass);


--
-- TOC entry 4908 (class 2604 OID 17934)
-- Name: exercise id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercise ALTER COLUMN id SET DEFAULT nextval('public.exercise_id_seq'::regclass);


--
-- TOC entry 4909 (class 2604 OID 17935)
-- Name: exerciseofuser id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exerciseofuser ALTER COLUMN id SET DEFAULT nextval('public.exerciseofuser_id_seq'::regclass);


--
-- TOC entry 4911 (class 2604 OID 17936)
-- Name: hashtag id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtag ALTER COLUMN id SET DEFAULT nextval('public.hashtag_id_seq'::regclass);


--
-- TOC entry 4912 (class 2604 OID 17937)
-- Name: hashtagofdish id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtagofdish ALTER COLUMN id SET DEFAULT nextval('public.hashtagofdish_id_seq'::regclass);


--
-- TOC entry 4913 (class 2604 OID 17938)
-- Name: healthstatus id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.healthstatus ALTER COLUMN id SET DEFAULT nextval('public.healthstatus_id_seq'::regclass);


--
-- TOC entry 4914 (class 2604 OID 17939)
-- Name: healthstatususer id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.healthstatususer ALTER COLUMN id SET DEFAULT nextval('public.healthstatususer_id_seq'::regclass);


--
-- TOC entry 4915 (class 2604 OID 17940)
-- Name: importanthashtag id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importanthashtag ALTER COLUMN id SET DEFAULT nextval('public.importanthashtag_id_seq'::regclass);


--
-- TOC entry 4916 (class 2604 OID 17941)
-- Name: ingredient id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredient ALTER COLUMN id SET DEFAULT nextval('public.ingredient_id_seq'::regclass);


--
-- TOC entry 4917 (class 2604 OID 17942)
-- Name: ingredientindish id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredientindish ALTER COLUMN id SET DEFAULT nextval('public.ingredientindish_id_seq'::regclass);


--
-- TOC entry 4918 (class 2604 OID 17943)
-- Name: levelexercise id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.levelexercise ALTER COLUMN id SET DEFAULT nextval('public.levelexercise_id_seq'::regclass);


--
-- TOC entry 4919 (class 2604 OID 17944)
-- Name: limitfood id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.limitfood ALTER COLUMN id SET DEFAULT nextval('public.limitfood_id_seq'::regclass);


--
-- TOC entry 4920 (class 2604 OID 17945)
-- Name: limitfooduser id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.limitfooduser ALTER COLUMN id SET DEFAULT nextval('public.limitfooduser_id_seq'::regclass);


--
-- TOC entry 4921 (class 2604 OID 17946)
-- Name: mealofuser id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mealofuser ALTER COLUMN id SET DEFAULT nextval('public.mealofuser_id_seq'::regclass);


--
-- TOC entry 4923 (class 2604 OID 17947)
-- Name: notification id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification ALTER COLUMN id SET DEFAULT nextval('public.notification_id_seq'::regclass);


--
-- TOC entry 4926 (class 2604 OID 17948)
-- Name: requiredindex id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.requiredindex ALTER COLUMN id SET DEFAULT nextval('public.requiredindex_id_seq'::regclass);


--
-- TOC entry 4927 (class 2604 OID 17949)
-- Name: unitdrink id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unitdrink ALTER COLUMN id SET DEFAULT nextval('public.unitdrink_id_seq'::regclass);


--
-- TOC entry 4928 (class 2604 OID 17950)
-- Name: userinfo id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userinfo ALTER COLUMN id SET DEFAULT nextval('public.userinfo_id_seq'::regclass);


--
-- TOC entry 4930 (class 2606 OID 17952)
-- Name: account account_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- TOC entry 4932 (class 2606 OID 17954)
-- Name: activitylevel activitylevel_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activitylevel
    ADD CONSTRAINT activitylevel_pkey PRIMARY KEY (id);


--
-- TOC entry 4934 (class 2606 OID 17956)
-- Name: diet diet_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.diet
    ADD CONSTRAINT diet_pkey PRIMARY KEY (id);


--
-- TOC entry 4936 (class 2606 OID 17958)
-- Name: dish dish_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dish
    ADD CONSTRAINT dish_pkey PRIMARY KEY (id);


--
-- TOC entry 4938 (class 2606 OID 17960)
-- Name: drinkofuser drinkofuser_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drinkofuser
    ADD CONSTRAINT drinkofuser_pkey PRIMARY KEY (id);


--
-- TOC entry 4940 (class 2606 OID 17962)
-- Name: exercise exercise_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercise
    ADD CONSTRAINT exercise_pkey PRIMARY KEY (id);


--
-- TOC entry 4942 (class 2606 OID 17964)
-- Name: exerciseofuser exerciseofuser_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exerciseofuser
    ADD CONSTRAINT exerciseofuser_pkey PRIMARY KEY (id);


--
-- TOC entry 4944 (class 2606 OID 17966)
-- Name: hashtag hashtag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtag
    ADD CONSTRAINT hashtag_pkey PRIMARY KEY (id);


--
-- TOC entry 4946 (class 2606 OID 17968)
-- Name: hashtagofdish hashtagofdish_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtagofdish
    ADD CONSTRAINT hashtagofdish_pkey PRIMARY KEY (id);


--
-- TOC entry 4948 (class 2606 OID 17970)
-- Name: healthstatus healthstatus_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.healthstatus
    ADD CONSTRAINT healthstatus_pkey PRIMARY KEY (id);


--
-- TOC entry 4950 (class 2606 OID 17972)
-- Name: healthstatususer healthstatususer_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.healthstatususer
    ADD CONSTRAINT healthstatususer_pkey PRIMARY KEY (id);


--
-- TOC entry 4952 (class 2606 OID 17974)
-- Name: importanthashtag importanthashtag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importanthashtag
    ADD CONSTRAINT importanthashtag_pkey PRIMARY KEY (id);


--
-- TOC entry 4954 (class 2606 OID 17976)
-- Name: ingredient ingredient_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredient
    ADD CONSTRAINT ingredient_pkey PRIMARY KEY (id);


--
-- TOC entry 4956 (class 2606 OID 17978)
-- Name: ingredientindish ingredientindish_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredientindish
    ADD CONSTRAINT ingredientindish_pkey PRIMARY KEY (id);


--
-- TOC entry 4958 (class 2606 OID 17980)
-- Name: levelexercise levelexercise_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.levelexercise
    ADD CONSTRAINT levelexercise_pkey PRIMARY KEY (id);


--
-- TOC entry 4960 (class 2606 OID 17982)
-- Name: limitfood limitfood_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.limitfood
    ADD CONSTRAINT limitfood_pkey PRIMARY KEY (id);


--
-- TOC entry 4962 (class 2606 OID 17984)
-- Name: limitfooduser limitfooduser_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.limitfooduser
    ADD CONSTRAINT limitfooduser_pkey PRIMARY KEY (id);


--
-- TOC entry 4964 (class 2606 OID 17986)
-- Name: mealofuser mealofuser_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mealofuser
    ADD CONSTRAINT mealofuser_pkey PRIMARY KEY (id);


--
-- TOC entry 4966 (class 2606 OID 17988)
-- Name: notification notification_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_pkey PRIMARY KEY (id);


--
-- TOC entry 4968 (class 2606 OID 17990)
-- Name: requiredindex requiredindex_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.requiredindex
    ADD CONSTRAINT requiredindex_pkey PRIMARY KEY (id);


--
-- TOC entry 4970 (class 2606 OID 17992)
-- Name: unitdrink unitdrink_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unitdrink
    ADD CONSTRAINT unitdrink_pkey PRIMARY KEY (id);


--
-- TOC entry 4972 (class 2606 OID 17994)
-- Name: userinfo userinfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userinfo
    ADD CONSTRAINT userinfo_pkey PRIMARY KEY (id);


--
-- TOC entry 4973 (class 2606 OID 17995)
-- Name: drinkofuser drinkofuser_unitdrinkid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drinkofuser
    ADD CONSTRAINT drinkofuser_unitdrinkid_fkey FOREIGN KEY (unitdrinkid) REFERENCES public.unitdrink(id);


--
-- TOC entry 4974 (class 2606 OID 18000)
-- Name: drinkofuser drinkofuser_userinfoid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drinkofuser
    ADD CONSTRAINT drinkofuser_userinfoid_fkey FOREIGN KEY (userinfoid) REFERENCES public.userinfo(id);


--
-- TOC entry 4983 (class 2606 OID 18005)
-- Name: ingredientindish fk_dish; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredientindish
    ADD CONSTRAINT fk_dish FOREIGN KEY (dishid) REFERENCES public.dish(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4977 (class 2606 OID 18010)
-- Name: hashtagofdish fk_dish; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtagofdish
    ADD CONSTRAINT fk_dish FOREIGN KEY (dishid) REFERENCES public.dish(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4985 (class 2606 OID 18015)
-- Name: levelexercise fk_exercise; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.levelexercise
    ADD CONSTRAINT fk_exercise FOREIGN KEY (exerciseid) REFERENCES public.exercise(id) ON DELETE CASCADE;


--
-- TOC entry 4975 (class 2606 OID 18020)
-- Name: exerciseofuser fk_exerciseofuser_userinfo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exerciseofuser
    ADD CONSTRAINT fk_exerciseofuser_userinfo FOREIGN KEY (userinfoid) REFERENCES public.userinfo(id);


--
-- TOC entry 4978 (class 2606 OID 18025)
-- Name: hashtagofdish fk_hashtag; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtagofdish
    ADD CONSTRAINT fk_hashtag FOREIGN KEY (hashtagid) REFERENCES public.hashtag(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4984 (class 2606 OID 18030)
-- Name: ingredientindish fk_ingredient; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredientindish
    ADD CONSTRAINT fk_ingredient FOREIGN KEY (ingredientid) REFERENCES public.ingredient(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4976 (class 2606 OID 18035)
-- Name: exerciseofuser fk_level_exercise; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exerciseofuser
    ADD CONSTRAINT fk_level_exercise FOREIGN KEY (levelexerciseid) REFERENCES public.levelexercise(id) ON DELETE CASCADE;


--
-- TOC entry 4979 (class 2606 OID 18040)
-- Name: healthstatususer healthstatususer_healthstatusid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.healthstatususer
    ADD CONSTRAINT healthstatususer_healthstatusid_fkey FOREIGN KEY (healthstatusid) REFERENCES public.healthstatus(id);


--
-- TOC entry 4980 (class 2606 OID 18045)
-- Name: healthstatususer healthstatususer_userinfoid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.healthstatususer
    ADD CONSTRAINT healthstatususer_userinfoid_fkey FOREIGN KEY (userinfoid) REFERENCES public.userinfo(id);


--
-- TOC entry 4981 (class 2606 OID 18050)
-- Name: importanthashtag importanthashtag_hashtagid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importanthashtag
    ADD CONSTRAINT importanthashtag_hashtagid_fkey FOREIGN KEY (hashtagid) REFERENCES public.hashtag(id) ON DELETE CASCADE;


--
-- TOC entry 4982 (class 2606 OID 18055)
-- Name: importanthashtag importanthashtag_requiredindexid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.importanthashtag
    ADD CONSTRAINT importanthashtag_requiredindexid_fkey FOREIGN KEY (requiredindexid) REFERENCES public.requiredindex(id) ON DELETE CASCADE;


--
-- TOC entry 4986 (class 2606 OID 18060)
-- Name: limitfooduser limitfooduser_limitfoodid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.limitfooduser
    ADD CONSTRAINT limitfooduser_limitfoodid_fkey FOREIGN KEY (limitfoodid) REFERENCES public.limitfood(id);


--
-- TOC entry 4987 (class 2606 OID 18065)
-- Name: limitfooduser limitfooduser_userinfoid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.limitfooduser
    ADD CONSTRAINT limitfooduser_userinfoid_fkey FOREIGN KEY (userinfoid) REFERENCES public.userinfo(id);


--
-- TOC entry 4988 (class 2606 OID 18070)
-- Name: mealofuser mealofuser_dishid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mealofuser
    ADD CONSTRAINT mealofuser_dishid_fkey FOREIGN KEY (dishid) REFERENCES public.dish(id);


--
-- TOC entry 4989 (class 2606 OID 18075)
-- Name: mealofuser mealofuser_userinfoid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mealofuser
    ADD CONSTRAINT mealofuser_userinfoid_fkey FOREIGN KEY (userinfoid) REFERENCES public.userinfo(id);


--
-- TOC entry 4990 (class 2606 OID 18080)
-- Name: requiredindex requiredindex_userinfoid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.requiredindex
    ADD CONSTRAINT requiredindex_userinfoid_fkey FOREIGN KEY (userinfoid) REFERENCES public.userinfo(id);


--
-- TOC entry 4991 (class 2606 OID 18085)
-- Name: userinfo userinfo_accountid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userinfo
    ADD CONSTRAINT userinfo_accountid_fkey FOREIGN KEY (accountid) REFERENCES public.account(id);


--
-- TOC entry 4992 (class 2606 OID 18090)
-- Name: userinfo userinfo_activitylevelid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userinfo
    ADD CONSTRAINT userinfo_activitylevelid_fkey FOREIGN KEY (activitylevelid) REFERENCES public.activitylevel(id);


--
-- TOC entry 4993 (class 2606 OID 18095)
-- Name: userinfo userinfo_dietid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userinfo
    ADD CONSTRAINT userinfo_dietid_fkey FOREIGN KEY (dietid) REFERENCES public.diet(id);


-- Completed on 2026-01-12 22:12:57

--
-- PostgreSQL database dump complete
--

