import boto3
import argparse


def parse_refs(refs):
    return {
        ref.split('=')[0]: ref.split('=')[1] for ref in refs
    }


def create_environment_options_string(job_definition):
    return " ".join(["-e {}={}".format(env['name'], env['value']) for env in job_definition['containerProperties']['environment']])


def create_command_string(job_definition, ref_map):
    def reference_refs(value: str):
        if value.startswith('Ref::'):
            return ref_map[value.replace('Ref::', '')]
        return value
    return " ".join(map(reference_refs, job_definition['containerProperties']['command']))


def main():
    parser = argparse.ArgumentParser('AWS Batch local running support tool')
    parser.add_argument('--job-definition-name', '-j', dest='job_definition_name', help='AWS Batch Job Definition Name')
    parser.add_argument('--revision', '-v', type=int, help='AWS Batch Job Definition Revision')
    parser.add_argument('--ref', '-r', dest='refs', action='append', help='AWS Batch replace Ref::hoge in command')

    args = parser.parse_args()

    ref_map = parse_refs(args.refs)

    session = boto3.Session()

    client = session.client('batch')

    response = client.describe_job_definitions(jobDefinitionName=args.job_definition_name)
    job_definitions = response['jobDefinitions']

    if args.revision is None:
        job_definition = max(job_definitions, key=lambda x: int(x['revision']))
    else:
        job_definition = list(filter(lambda x: x['revision'] == args.revision, job_definitions))
    environment_options = create_environment_options_string(job_definition)
    image = job_definition['containerProperties']['image']
    command = create_command_string(job_definition, ref_map)

    print('docker run --rm -it {} {} "{}"'.format(environment_options, image, command))


if __name__ == '__main__':
    main()
