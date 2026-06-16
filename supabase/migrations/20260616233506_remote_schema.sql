drop extension if exists "pg_net";

grant delete on table "public"."events" to "anon";

grant insert on table "public"."events" to "anon";

grant select on table "public"."events" to "anon";

grant update on table "public"."events" to "anon";

grant delete on table "public"."events" to "authenticated";

grant insert on table "public"."events" to "authenticated";

grant select on table "public"."events" to "authenticated";

grant update on table "public"."events" to "authenticated";

grant delete on table "public"."events" to "service_role";

grant insert on table "public"."events" to "service_role";

grant select on table "public"."events" to "service_role";

grant update on table "public"."events" to "service_role";
